import os
import time
import json
import sys
import pymupdf
import asyncio
import boto3
import io
from dotenv import load_dotenv
from PIL import Image

cur_path=os.getcwd()
cur_path=cur_path.replace("ai_core/CreateImageKnowledgeBase", "")

#PROD
os.environ['AWS_ACCESS_KEY_ID'] = ''
os.environ['AWS_SECRET_ACCESS_KEY'] = ''
os.environ['S3_BUCKET_NAME'] = ''
os.environ['OPENAI_API_KEY']=''
os.environ['AWS_DEFAULT_REGION'] = 'us-west-2'

def list_files(bucket_name, prefix, s3_client, file_type=".pdf"):
    """
    Lists all files in the specified S3 bucket under the given prefix.
    
    Args:
        bucket_name (str): Name of the S3 bucket.
        prefix (str): Prefix (folder path) within the bucket.
        s3_client (boto3.client): S3 client object.
        file_type (str, optional): File type to filter. Defaults to ".pdf".
    
    Returns:
        list: List of PDF file names.
    """
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='KNOWLEDGEBASE/' + prefix
        )

        files = [content['Key'].split("/")[-1] for content in response.get('Contents', []) if content['Key'].lower().endswith(file_type)]
        return files
    except Exception as e:
        print("Error: Could not list files from S3 bucket:", e)
        return []

def load_json(bucket_name, folder_name, file_name, s3_client):
    """
    Loads a JSON file from the specified S3 bucket.
    
    Args:
        bucket_name (str): Name of the S3 bucket.
        folder_name (str): Folder name within the bucket.
        file_name (str): Name of the JSON file.
        s3_client (boto3.client): S3 client object.
    
    Returns:
        dict: JSON data.
    """
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=f"{folder_name}/{file_name}")
        json_data = response['Body'].read().decode('utf-8')
        data = json.loads(json_data)
        return data
    except Exception as e:
        print("Error: Could not load JSON file from S3 bucket:", e, " - ", folder_name, " - ", file_name)
        return {}

def convert_pixmap_to_image(pixmap):
    """
    Converts a pixmap to a PIL Image object.
    
    Args:
        pixmap (PyMuPDF.Pixmap): Pixmap object.
    
    Returns:
        io.BytesIO: Image buffer.
    """
    try:
        image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples, "raw", "RGB", 0, 1)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer
    except Exception as e:
        print("Error: Could not convert pixmap to image:", e)
        return None

async def extract_cropped_images(raw_json, pdf_name, bucket_name, BU_Name, s3_client):
    """
    Extracts cropped images from a PDF file based on the provided JSON data.
    
    Args:
        raw_json (dict): Raw JSON data.
        pdf_name (str): Name of the PDF file.
        bucket_name (str): Name of the S3 bucket.
        BU_Name (str): Business unit name.
        s3_client (boto3.client): S3 client object.
    
    Returns:
        str: Success or error message.
    """
    print(pdf_name)
    # try:
    #     print(pdf_name)
    #     response = s3_client.get_object(Bucket=bucket_name, Key=f"KNOWLEDGEBASE/{BU_Name}/{pdf_name}")
    #     pdf_data = response['Body'].read()
    #     pdf_stream = io.BytesIO(pdf_data)
    #     doc = pymupdf.open(stream=pdf_stream, filetype="pdf")  # open document
    # except Exception as e:
    #     print("Error: Could not open the PDF file:", e)
    #     return "Error: Could not open the PDF file"

    image_coordinate_dict = {}
    figure_blocks = []
    for block in raw_json['Blocks']:
        Page_Number = block['Page']

        if block['BlockType'] == 'LAYOUT_FIGURE':
            figure_blocks.append(block)
            image_coordinate_dict[Page_Number] = block['Geometry']['BoundingBox']

    image_number = 0
    for figure_block in figure_blocks:
        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=f"KNOWLEDGEBASE/{BU_Name}/{pdf_name}")
            pdf_data = response['Body'].read()
            pdf_stream = io.BytesIO(pdf_data)
            doc = pymupdf.open(stream=pdf_stream, filetype="pdf")  # open document
        except Exception as e:
            print("Error: Could not open the PDF file:", e)
            return "Error: Could not open the PDF file"
        page = doc[figure_block['Page'] - 1]

        page_height = page.rect.height
        page_width = page.rect.width

        image_width = figure_block['Geometry']['BoundingBox']['Width']
        image_height = figure_block['Geometry']['BoundingBox']['Height']
        image_area = image_width * image_height

        width = (page_width * image_width) + (figure_block['Geometry']['BoundingBox']['Left'] * page_width)
        height = (page_height * image_height) + (figure_block['Geometry']['BoundingBox']['Top'] * page_height)
        
        try:
            page.set_cropbox(pymupdf.Rect(figure_block['Geometry']['BoundingBox']['Left'] * page_width, figure_block['Geometry']['BoundingBox']['Top'] * page_height, width, height))
            pix = page.get_pixmap(dpi=600)
            image_buffer = convert_pixmap_to_image(pix)
            flder_name = "".join(pdf_name.split(".")[:-1])
            
            if image_area > 0.01:
                s3_client.upload_fileobj(image_buffer, bucket_name, f"KnowledgeBase_Images/{BU_Name}/{flder_name}/page_{page.number + 1}_image_{image_number}.png")
                print("Stored successfully")
            else:
                print("Image Excluded")
                s3_client.upload_fileobj(image_buffer, bucket_name, f"KnowledgeBase_Images_Archive/{BU_Name}/{flder_name}/page_{page.number + 1}_excluded_image_{image_number}.png")
            
            image_number += 1
        except Exception as e:
            print("Error: Could not process image:", e)

    return "Successfully extracted images"

async def process_pdf(bucket_name, BU_Name, file_name, s3_client):
    """
    Processes a PDF file to extract cropped images.
    
    Args:
        bucket_name (str): Name of the S3 bucket.
        BU_Name (str): Business unit name.
        file_name (str): Name of the PDF file.
        s3_client (boto3.client): S3 client object.
    """
    extracts_flder_name = "".join(file_name.split(".")[:-1])
    json_data = load_json(bucket_name=bucket_name, folder_name=f"KnowledgeBase_Extracts/{BU_Name}/{extracts_flder_name}", file_name="Raw_Textract_Output.json", s3_client=s3_client)
    await extract_cropped_images(json_data, file_name, bucket_name, BU_Name, s3_client)

async def save_images(s3_client, bucket_name, KnowledgeBaseName, specific_pdf_list=[]):
    """
    Saves cropped images from PDF files in the specified S3 bucket.
    
    Args:
        s3_client (boto3.client): S3 client object.
        bucket_name (str): Name of the S3 bucket.
        KnowledgeBaseName (str): Name of the knowledge base.
    """
    if specific_pdf_list!=[]:
        pdf_files_lst = specific_pdf_list
    else:
        pdf_files_lst = list_files(bucket_name=bucket_name, prefix=KnowledgeBaseName, s3_client=s3_client, file_type=".pdf")
    tasks = [asyncio.create_task(process_pdf(bucket_name=bucket_name, BU_Name=KnowledgeBaseName, file_name=pdf_file, s3_client=s3_client)) for pdf_file in pdf_files_lst]
    await asyncio.gather(*tasks)
