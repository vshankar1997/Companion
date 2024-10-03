import os
from dotenv import load_dotenv
from openai import OpenAI
import boto3
import pickle
from pymilvus import (
    connections,
    CollectionSchema,
    FieldSchema,
    DataType,
    Collection,
    utility
)
load_dotenv()

# Get current working directory
cur_path = os.getcwd()
cur_path = cur_path.replace("ai_core/CreateImageKnowledgeBase", "")

# Set environment variables
#PROD
os.environ['AWS_ACCESS_KEY_ID'] = ''
os.environ['AWS_SECRET_ACCESS_KEY'] = ''
os.environ['S3_BUCKET_NAME'] = ''
os.environ['OPENAI_API_KEY']=''
os.environ['AWS_DEFAULT_REGION'] = ''
os.environ['MILVUS_HOST'] = '' # milvus server host
os.environ['MILVUS_PORT'] = '' # milvus server port

# create an s3 client
s3_client = boto3.client('s3')

# name of knowledgebase which is collection name as well
# put correct knowledge base name (should be in capital letters) - same as in milvus knowledge base db.

KnowledgeBaseName = "TARLATAMAB"


CollectionName=KnowledgeBaseName+"_IMAGES"
bucket_name = os.environ["S3_BUCKET_NAME"]

# create an OpenAI client
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def embedding_request(text):
    """
    Generates an embedding for the given text using OpenAI's text-embedding-3-small model.
    Args:
        text (str): The input text.

    Returns:
        list: The embedding vector.
    """
    response = (
        client.embeddings.create(input=text, model="text-embedding-3-small")
        .data[0]
        .embedding
    )
    return response

def list_and_load_pkl_files(KnowledgeBaseName):
    """
    Lists all .pkl files in the specified S3 bucket under the given prefix and loads the objects from the files.
    Args:
        KnowledgeBaseName (str): Name of the knowledge base.

    Returns:
        list: List of loaded objects from the .pkl files.
    """
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='KnowledgeBase_Images/'+KnowledgeBaseName+"/"
        )

        pkl_files = [content['Key'] for content in response.get('Contents', []) if content['Key'].lower().endswith('.pkl')]

        print("Number of files - ", len(pkl_files))
        # Initialize a list to hold the loaded objects from .pkl files
        loaded_objects = []
        # Iterate through the list of .pkl file paths
        for path in pkl_files:
            print('reading for path = ', path)
            response = s3_client.get_object(Bucket=os.environ["S3_BUCKET_NAME"], Key=path)
            # read the content of pkl file
            pkl_content = response['Body'].read()
            # Load the document_instances list
            loaded_obj = pickle.loads(pkl_content)
            loaded_objects.append(loaded_obj)

        print("Number of objects - ", len(loaded_objects))
        return loaded_objects
    except Exception as e:
        print("Error: ", str(e))

def prepare_milvus_data(KnowledgeBaseName):
    """
    Prepares the data for Milvus by loading the .pkl files, embedding the image text, and adding additional fields.
    Args:
        KnowledgeBaseName (str): Name of the knowledge base.

    Returns:
        list: List of dictionaries representing the Milvus input data.
    """
    try:
        pkl_objects = list_and_load_pkl_files(KnowledgeBaseName)

        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix='KnowledgeBase_Images/'+KnowledgeBaseName+"/")

        all_files = [content['Key'].split(bucket_name)[-1].strip("/") for content in response.get('Contents', [])]
        milvus_input_data = []
        id = 1
        for lst in pkl_objects:
            for chunk in lst:
                image_path = chunk['image_path']
                if image_path in all_files:

                    if chunk.get('Title') == None:
                        chunk['Title'] = 'Unknown'

                        print("Title not found for - ", image_path)

                    if chunk.get('Caption') == None:
                        chunk['Caption'] = 'Unknown'
                        print("Caption not found for - ", image_path)
                    pass
                else:
                    # Image is not present at image path
                    print("Image not found at - ", image_path)
                    continue
                chunk['vector'] = embedding_request(chunk['Image_Text'])
                chunk['img_id'] = id
                milvus_input_data.append(chunk)
                id += 1
        return milvus_input_data
    except Exception as e:
        print("Error: ", str(e))

def upload_and_add_documents_to_milvusdb(KnowledgeBaseName, CollectionName):
    """
    Uploads and adds documents to Milvus database.
    Args:
        KnowledgeBaseName (str): Name of the knowledge base.
        CollectionName (str): Name of the collection in Milvus.

    Returns:
        None
    """
    try:
        milvus_data = prepare_milvus_data(KnowledgeBaseName)
        conn = connections.connect(
            host=os.environ["MILVUS_HOST"], port=os.environ["MILVUS_PORT"], secure=False
        )
        id = FieldSchema(
            name="id",
            dtype=DataType.INT64,
            is_primary=True,
            auto_id=True
        )
        img_id = FieldSchema(
            name="img_id",
            dtype=DataType.INT64,
            is_primary=False,
        )
        Image_Text = FieldSchema(
            name="Image_Text", dtype=DataType.VARCHAR, max_length=65000, default_value="Unknown"
        )
        vector = FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1536)
        PDF_Name = FieldSchema(
            name="PDF_Name",
            dtype=DataType.VARCHAR,
            max_length=1000,
            default_value="Unknown",
        )
        Page_Number = FieldSchema(
            name="Page_Number",
            dtype=DataType.INT64,
            default_value="Unknown",
        )
        Image_Number = FieldSchema(
            name="Image_Number",
            dtype=DataType.INT64,
            default_value="Unknown",
        )
        image_path = FieldSchema(
            name="image_path",
            dtype=DataType.VARCHAR,
            max_length=5000,
            default_value="Unknown",
        )
        Title = FieldSchema(
            name="Title",
            dtype=DataType.VARCHAR,
            max_length=20000,
            default_value="Unknown",
        )
        Caption = FieldSchema(
            name="Caption",
            dtype=DataType.VARCHAR,
            max_length=20000,
            default_value="Unknown",
        )
        pdf_path = FieldSchema(
            name="pdf_path",
            dtype=DataType.VARCHAR,
            max_length=30000,
            default_value="Unknown",
        )

        schema = CollectionSchema(
            fields=[id, img_id, Image_Text, vector, PDF_Name, Page_Number, Image_Number, image_path, Title, Caption, pdf_path],
            description=f"Collection of images from KnowledgeBase documents for Amgen - {KnowledgeBaseName}",
            enable_dynamic_field=True,
        )
        collection_name = CollectionName

        collection = Collection(
            name=collection_name, schema=schema, using="default", shards_num=2
        )
        collection = Collection(collection_name)

        index_params = {
            "index_type": "HNSW",
            "metric_type": "L2",
            "params": {"M": 16, "efConstruction": 64},
        }

        collection.create_index(
            field_name="vector",
            index_params=index_params,
            index_name=collection_name + "_index",
        )
        collection.load()

        collection.insert(milvus_data)
        collection.load()

        if utility.has_collection(collection_name):
            status = 'Success'
        else:
            status = "Error"
        print("status - ", status)
    except Exception as e:
        print("Error: ", str(e))

upload_and_add_documents_to_milvusdb(KnowledgeBaseName, CollectionName)