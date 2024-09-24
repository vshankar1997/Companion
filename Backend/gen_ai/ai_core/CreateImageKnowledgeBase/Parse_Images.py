import os
import time
import json
import pymupdf
import base64
from openai import OpenAI, AsyncOpenAI
import pickle
import boto3
import io, asyncio
from Extract_Cropped_Images import save_images
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get current working directory
cur_path = os.getcwd()
cur_path = cur_path.replace("ai_core/CreateImageKnowledgeBase", "")

# Initialize OpenAI client
async_client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Initialize S3 client
s3_client = boto3.client('s3')

# Name of the knowledge base
# put correct knowledge base name (should be in capital letters) - same as in milvus knowledge base db.
KnowledgeBaseName = "TEPEZZA"

# S3 bucket name
s3_bucket_name = os.environ["S3_BUCKET_NAME"]

# System prompt for AI assistant
system_prompt_w_title = '''
You are an AI assistant that analyzes the Image and give accurate descriptions of images.
Follow these steps to describe the image within the red border box:
1. Go through the Entire Image carefully and fully comprehend it.
2. Keeping in mind the learnings and understanding from the image. carefully analyze the portion of the image under the highlightd red box.
3. Now Provide a detailed description of the content present with in the highlighted red Box 
4. Explain the image in text and extract all details from the image.
5. If Image contains a table then extract the table data as well.
6. Explain the graphs and flowcharts as well without missing any details.
7. Make sure to give the caption of the image only if it is present.
8. Also provide summary of the image in the red border box.

IMPORTANT: Make sure to provide the description of the content present within the red box only. Be as verbose as possible.

Generate short summary of the image based on the content present in the red box.
Summary: <Summary of the Image>

Generate a small title of the image based on the content present in the red box or give the caption of the marked image as title if already present.

Output Format - 

Title: <Title of the Image>
'''

def list_files(bucket_name, prefix, s3_client, file_type=".pdf"):
    """
    Lists all files in the specified S3 bucket under the given prefix.
    Args:
        bucket_name (str): Name of the S3 bucket.
        prefix (str): Prefix (folder path) within the bucket.

    Returns:
        list: List of PDF file names.
    """
    response = s3_client.list_objects_v2(
        Bucket=bucket_name,
        Prefix='KNOWLEDGEBASE/'+prefix)

    files = [content['Key'].split("/")[-1] for content in response.get('Contents', []) if content['Key'].lower().endswith(file_type)]
    return files


def list_folders(bucket_name, folder_name, s3_client):
    """
    Lists all files in the specified S3 bucket under the given prefix.
    Args:
        bucket_name (str): Name of the S3 bucket.
        prefix (str): Prefix (folder path) within the bucket.

    Returns:
        list: List of PDF file names.
    """
    response = s3_client.list_objects_v2(
        Bucket=bucket_name,
        Prefix=folder_name, Delimiter='/')
    
    folders = [common_prefix['Prefix'].split(folder_name)[-1].strip("/") for common_prefix in response.get('CommonPrefixes', [])]
    return folders

def load_json(bucket_name, folder_name, file_name, s3_client):
    """
    Loads a JSON file from S3 bucket.
    Args:
        bucket_name (str): Name of the S3 bucket.
        folder_name (str): Folder path within the bucket.
        file_name (str): Name of the JSON file.
        s3_client: S3 client object.

    Returns:
        dict: JSON data.
    """
    response = s3_client.get_object(Bucket=bucket_name, Key=f"{folder_name}/{file_name}")
    json_data = response['Body'].read().decode('utf-8')
    data = json.loads(json_data)
    return data

def encode_image(bytes_obj):
    """
    Encodes image bytes to base64 format.
    Args:
        bytes_obj: Image bytes.

    Returns:
        str: Base64 encoded image.
    """
    return base64.b64encode(bytes_obj).decode("utf-8")

async def analyze_image_in_image(image, system_prompt):
    """
    Analyzes the given image using OpenAI API.
    Args:
        image (str): Base64 encoded image.
        system_prompt (str): System prompt for AI assistant.

    Returns:
        str: AI-generated image description.
    """
    response = await async_client.chat.completions.create(
        model="gpt-4o",
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Parse the figure marked in given image and extract all the content from the figure. Be as verbose as possible. Parse and extract all graphs and charts if present and write them in text as well. Don't miss to generate title as in '''Title: <Title of the Image>''' format and caption as '''Caption: <Caption of the Image>''' format."
                    },
                    {
                        "type": "image_url", "image_url": {
                            "url": f"data:image/png;base64,{image}",
                            "detail": "high"}
                    },
                ],
            }
        ],
        max_tokens=4096,
    )

    return response.choices[0].message.content

def page_image_bytes_w_border(fig_block, page, image_num):
    """
    Extracts the image bytes with a red border from the given figure block and page.
    Args:
        fig_block (dict): Figure block from Textract output.
        page (pymupdf.Page): Page object from PyMuPDF.
        image_num (int): Image number.

    Returns:
        tuple: Base64 encoded image and page number.
    """
    print("page number - : ", page.number+1)
    print("image number - : ", image_num)
    # Get the height and width of the page
    page_height = page.rect.height
    page_width = page.rect.width

    image_width  = fig_block['Geometry']['BoundingBox']['Width']
    image_height = fig_block['Geometry']['BoundingBox']['Height']
    image_area = image_width * image_height
    if image_area <= 0.01:
        return ""

    width = (page_width * image_width) + (fig_block['Geometry']['BoundingBox']['Left'] * page_width)
    height = (page_height * image_height) + (fig_block['Geometry']['BoundingBox']['Top'] * page_height)
    padding = 5  # Define a padding value, adjust as needed

    # Adjusted rectangle coordinates with padding
    left_with_padding = (fig_block['Geometry']['BoundingBox']['Left'] * page_width) - padding
    top_with_padding = (fig_block['Geometry']['BoundingBox']['Top'] * page_height) - padding
    right_with_padding = width + padding
    bottom_with_padding = height + padding

    # Create a new rectangle annotation with padding
    rect_with_padding = pymupdf.Rect(left_with_padding, top_with_padding, right_with_padding, bottom_with_padding)
    annot = page.add_rect_annot(rect_with_padding)

    # Set the fill and border colors
    annot.update()
    annot.set_border(width=2.5)
    annot.border_color = (1, 0, 0)  # red  
    annot.update()
    pix = page.get_pixmap(dpi=600)  # render page to an image
    bytes_obj = pix.tobytes()
    base64_image = encode_image(bytes_obj)
    page_number = page.number

    return (base64_image, page_number+1)

async def prepare_image_chunks(s3_bucket_name, KnowledgeBaseName, s3_client, img_file_name):
    """
    Prepares image chunks from the given folder of a knowledge base.
    Args:
        s3_bucket_name (str): Name of the S3 bucket.
        KnowledgeBaseName (str): Name of the knowledge base.
        s3_client: S3 client object.
        img_file_name (str): Name of the pdf file.

    Returns:
        list: List of image chunks.
    """
    img_folder_name = "".join(img_file_name.split(".")[:-1])
    raw_json = load_json(bucket_name=s3_bucket_name, folder_name=f"KnowledgeBase_Extracts/{KnowledgeBaseName}/{img_folder_name}", file_name="Raw_Textract_Output.json", s3_client=s3_client)
    
    print("Starting for ********************************************************************************************************************************")
    print("PDF File Name : ", img_file_name)
    
    image_chunks = []
    figure_blocks = []
    for block in raw_json['Blocks']:
        Page_Number = block['Page']
        
        if block['BlockType'] == 'LAYOUT_FIGURE':
            figure_blocks.append(block)
    
    image_number = 0
    for figure_block in figure_blocks:
        try:
            # Reading PDF File
            response = s3_client.get_object(Bucket=s3_bucket_name, Key=f"KNOWLEDGEBASE/{KnowledgeBaseName}/{img_file_name}")
            pdf_data = response['Body'].read()
            pdf_stream = io.BytesIO(pdf_data)
            doc = pymupdf.open(stream=pdf_stream, filetype="pdf")  # open document
        except Exception as e:
            print("Error: Could not open the PDF file")
            print(e)
            return []
        page = doc[figure_block['Page']-1]
        base64_image = ""
        chunk = {}
        try:
            print("Analyzing the image ->")
            base64_image, PageNumber = page_image_bytes_w_border(figure_block, page, image_number)
        except Exception as e:
            print("skipped image extraction")
            print(e)
        image_number += 1
        if base64_image == "":
            print("skipping image extraction because area is too small")
            continue
        time.sleep(0.2)
        try:
            res = await analyze_image_in_image(base64_image, system_prompt_w_title)
            formatted_res = res.replace("**", "")
            formatted_res = res.replace("##", "")

            title_start = formatted_res.find("Title:")
            if title_start != -1:
                title_end = formatted_res.find("\n", title_start)
                if title_end != -1:
                    title = formatted_res[title_start + len("Title:"):title_end].strip()
                    chunk["Title"] = title
                else:
                    chunk["Title"] = ""
            else:
                chunk["Title"] = ""

            caption_start = formatted_res.find("Caption:")
            if caption_start != -1:
                caption_end = formatted_res.find("\n", caption_start)
                if caption_end != -1:
                    Caption = formatted_res[caption_start + len("Caption:"):caption_end].strip()
                    chunk["Caption"] = Caption
                else:
                    chunk["Caption"] = ""
            else:
                chunk["Caption"] = ""

            chunk["Image_Text"] = res
            chunk["Image_Number"] = image_number-1
            chunk["Page_Number"] = PageNumber
            chunk['PDF_Name'] = img_file_name

            image_path = f"KnowledgeBase_Images/{KnowledgeBaseName}/{img_folder_name}/page_{PageNumber}_image_{image_number-1}.png"
            pdf_path = f"KNOWLEDGEBASE/{KnowledgeBaseName}/{img_file_name}"
            chunk['image_path'] = image_path
            chunk['pdf_path'] = pdf_path
            if chunk != {}:
                image_chunks.append(chunk)
            print("Successfully extracted images")
        except Exception as e:
            print("Error in analyzing the image")
            print(e)
    
    try:
        if image_chunks != []:
            chunk_pkl_obj = pickle.dumps(image_chunks)
            # Save the chunk as a pickle file
            object_key = 'KnowledgeBase_Images/'+KnowledgeBaseName+"/"+img_folder_name+"/"+'Image_Chunks.pkl'
            s3_client.put_object(Bucket=s3_bucket_name, Key=object_key, Body=chunk_pkl_obj)
            print("for doc, ", img_folder_name, " chunks stored")
        else:
            print("No Image Chunks found for - ", img_folder_name)
    except Exception as e:
        print("Error in storing chunks")
        print(e)
    
    return image_chunks

async def process_pdf(s3_bucket_name, KnowledgeBaseName, s3_client):
    """
    Processes PDF files in the knowledge base and extracts image chunks.
    Args:
        s3_bucket_name (str): Name of the S3 bucket.
        KnowledgeBaseName (str): Name of the knowledge base.
        s3_client: S3 client object.

    Returns:
        list: List of image chunks.
    """
    folder_name = f"KnowledgeBase_Images/{KnowledgeBaseName}/"
    img_folder_names = list_folders(s3_bucket_name, folder_name, s3_client)
    json_folder_name = f"KnowledgeBase_Extracts/{KnowledgeBaseName}/"
    json_file_names = list_folders(s3_bucket_name, json_folder_name, s3_client)
    pdf_file_names = list_files(s3_bucket_name, KnowledgeBaseName, s3_client, ".pdf")
    
    start_time = time.time()
    all_chunks = []
    tasks = []
    for file in pdf_file_names:
        folder = "".join(file.split(".")[:-1])
        if (folder in json_file_names) and (folder in img_folder_names):
            task = asyncio.create_task(prepare_image_chunks(s3_bucket_name, KnowledgeBaseName, s3_client, file))
            tasks.append(task)
        else:
            print("Folder not found in JSON or PDF files - ", folder)
            print("Document might not contain any images - ", file)
            
    all_chunks = await asyncio.gather(*tasks)
    end_time = time.time()
    print("parsing time taken - ", end_time-start_time)
    return all_chunks

# Main execution
try:
    print("Starting to extract images from PDF files")
    asyncio.run(save_images(s3_client, s3_bucket_name, KnowledgeBaseName))
    print("Successfully extracted all images")
    print()
    print("Starting to parse images and save chunks in pickle file")
    all_img_chunks = asyncio.run(process_pdf(s3_bucket_name, KnowledgeBaseName, s3_client))
except Exception as e:
    print("An error occurred:")
    print(e)