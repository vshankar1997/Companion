import os
import time
import pickle
import boto3
# from dotenv import load_dotenv
from pymilvus import connections,utility,Collection
from langchain.vectorstores import Milvus
from langchain.schema import Document
from langchain.embeddings.openai import OpenAIEmbeddings

os.environ['OPENAI_API_KEY']=''
os.environ['EMBEDDING_MODEL_NAME']='text-embedding-3-small'
# os.environ['S3_BUCKET_NAME'] = 'companion-app-document'
os.environ['S3_BUCKET_NAME'] = ''

# name of knowledgebase which is collection name as well
# KnowledgeBaseName = "UPLIZNA"
KnowledgeBaseName = "TED_GUIDEBOOK"
# cur_path=os.getcwd()
# cur_path=cur_path.replace("ai_core/CreateKnowledgeBase", "")

# dotenv_path= cur_path+'gen_ai/.env'
# dotenv_path='/var/snap/amazon-ssm-agent/7983/Genai/companion-ai/Backend/gen_ai/gen_ai/.env'
# load_dotenv(dotenv_path)

def list_pkl_files(bucket_name, s3_client):
    """
    Lists all PDF files in the specified S3 bucket under the given prefix.
    Args:
        bucket_name (str): Name of the S3 bucket.
        prefix (str): Prefix (folder path) within the bucket.

    Returns:
        list: List of PDF file names.
    """
    response = s3_client.list_objects_v2(
        Bucket=bucket_name,
        Prefix='KnowledgeBase_Extracts/'+KnowledgeBaseName+"/")

    pkl_files = [content['Key'] for content in response.get('Contents', []) if content['Key'].lower().endswith('.pkl')]
    return pkl_files

# create an s3 client
s3 = boto3.client('s3')

pkl_files_paths = list_pkl_files(os.environ["S3_BUCKET_NAME"], s3)


def convert_to_doc_instance(all_chunks):
    docs_schema = []
    for chunk in all_chunks:
        # For each item in the processed output, create a document instance
        document_instance = Document(
            page_content= chunk["Text"],
            metadata={
                "document_name": chunk["pdf_name"],
                "title": chunk["title"],
                "page_number": chunk["Page"],
                "author": chunk['Authors']
            })
        docs_schema.append(document_instance)
    return docs_schema

knowledgebase_chunks = []
for path in pkl_files_paths:
    print('reading for path = ', path)
    response = s3.get_object(Bucket=os.environ["S3_BUCKET_NAME"], Key=path)
    # read the content of pkl file
    pkl_content = response['Body'].read()
    # Load the document_instances list
    # with open(collection_db_name + '.pkl', 'rb') as f:
    knowledgebase_chunks += pickle.loads(pkl_content)
    loaded_document_instances = convert_to_doc_instance(knowledgebase_chunks)

print("Number of total chunks = ", len(loaded_document_instances))

embeddings = OpenAIEmbeddings(model=os.environ["EMBEDDING_MODEL_NAME"], chunk_size=15)
retry_count = 0
max_retries = 20
chunk_size = 100

for i in range(0, len(loaded_document_instances), chunk_size):
    document_chunk = loaded_document_instances[i:i+chunk_size]
    while retry_count < max_retries:
        try:
            # Create a Milvus collection from the documents and embeddings
            vector_db = Milvus.from_documents(
                document_chunk,
                embeddings,
                collection_name=KnowledgeBaseName,
                connection_args={"host": "localhost", "port": "19530"},
            )
            print("collection successfully created")
            break  # If the operation is successful, break the loop
        except :
            print("Rate limit exceeded. Waiting for 60 seconds before retrying.")
            time.sleep(60)  # Wait for 60 seconds
            retry_count += 1