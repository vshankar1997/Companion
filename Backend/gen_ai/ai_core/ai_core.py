import asyncio
import time
import logging
from pymilvus import connections, utility, Collection, DataType, CollectionSchema, FieldSchema
from django.conf import settings
from ai_core.openai_prompts import GenerateChatTitlePrompt
from ai_core.pdfParserTextract import process_files

import ai_core.agent_workflow as agent_workflow
import ai_core.openai_client as _openai_client

logger = logging.getLogger(__name__)

def own_chat_ai_call(prompt, chat, BU_Name, session_id, regenerate=False, is_upload=False, upload_documents=[]):
    """
    This function calls an AI model to generate responses based on the given prompt and chat history.
    
    Parameters:
    - prompt (str): The prompt for the AI model.
    - chat (list): The chat history.
    - BU_Name (str): The name of the business unit.
    - session_id (str): The session ID.
    - regenerate (bool): True to regenerate response for previous question.
    - is_upload (bool): True if the chat includes uploaded documents.
    - upload_documents (list): A list of uploaded documents.
    
    Returns:
    - msg (dict): A dictionary containing the AI-generated answer, the status of the operation, and the source of the answer.
    """
    try:
        answer, source, images, get_only_images, is_stream, generation_trace, trace = agent_workflow.get_knowledge_response(prompt, chat, BU_Name, regenerate, str(session_id), is_upload, upload_documents)
        
        # Check if the answer was successfully generated
        if answer:
            status = "Success"
        else:
            status = "Error"

        # Prepare the return message
        msg = {
            "message": answer, 
            "status": status, 
            "source": source, 
            "image_details": images,
            "get_only_images": get_only_images,
            "is_stream": is_stream, 
            # "generation_trace": generation_trace, 
            # "trace": trace
        }
        logger.info(f"Final AI response: {msg}")
        # Return the message
        return msg
        
    except Exception as e:
        # If an error occurs, raise it
        raise e

def extractPDFData(Pdf_Names):
    """
    This function extracts data from the given PDFs and creates a schema for each document.
    
    Parameters:
    - Pdf_Names (list): A list of PDFs from which data is to be extracted.
    
    Returns:
    - all_chunks (list): A list of document schemas with the actual chunks for the extracted data.
    - processed_output (dict): The processed output from the PDFs.
    """
    try:
        # Initialize an empty list for the documents schema
        processed_output_ = []
        
        # parallel adobe parsing (api calls via rest api)
        start_time = time.time()
        # json_output = asyncio.run(process_files(document_names=Pdf_Names))
        processed_output_, all_chunks = asyncio.run(process_files(settings.BUCKET_NAME, Pdf_Names, 'UPLOADED_DOCS/'))
        
        # Record the end time
        end_time = time.time()
        
        # Calculate the elapsed time    
        elapsed_time = end_time - start_time
        logger.info(f"Textract Processing time for uploaded docs: {elapsed_time:.2f} seconds")
        
        return all_chunks, processed_output_
    
    except Exception as e:
        # If an error occurs, raise it
        raise e

def vectorizePdfs(Pdfs, session_id):
    """
    This function vectorizes the given PDFs using OpenAI embeddings and stores them in a Milvus collection.
    
    Parameters:
    - Pdfs (list): A list of PDFs to be vectorized.
    - session_id (str): The session ID for the current session.
    
    Returns:
    - msg (dict): A dictionary containing the processed output and the status of the operation.
    """
    try:
        # Extract data from the PDFs
        start_time = time.time()
        docs_schema, processed_output = extractPDFData(Pdfs)
        
        # Record the end time
        end_time = time.time()
        
        # Calculate the elapsed time
        textract_extraction_time = end_time - start_time

        start_time = time.time()
        
        milvus_input_data = []
        
        for chunk in docs_schema:
            milvus_input_data.append({
                'chunk_id': chunk['chunk_id'],
                'text': chunk['Text'],
                'vector': _openai_client.embedding_request(chunk['Text']),
                'document_name': chunk["pdf_name"],
                'page_number': chunk["Page"],
                'author': chunk['Authors']
            })

        conn = connections.connect(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            secure=False,
        )

        id = FieldSchema(
            name="id",
            dtype=DataType.INT64,
            is_primary=True,
            auto_id=True,
        )

        chunk_id = FieldSchema(
            name="chunk_id",
            dtype=DataType.INT64,
            is_primary=False,
        )

        text = FieldSchema(
            name="text", 
            dtype=DataType.VARCHAR, 
            max_length=65000, 
            default_value="Unknown"
        )

        vector = FieldSchema(
            name="vector", 
            dtype=DataType.FLOAT_VECTOR, 
            dim=1536
        )

        document_name = FieldSchema(
            name="document_name",
            dtype=DataType.VARCHAR,
            max_length=1000,
            default_value="Unknown",
        )

        page_number = FieldSchema(
            name="page_number",
            dtype=DataType.INT64,
            default_value=0,
        )

        author = FieldSchema(
            name="author", 
            dtype=DataType.VARCHAR, 
            max_length=2000, 
            default_value="Unknown"
        )

        schema = CollectionSchema(
            fields=[id, chunk_id, text, vector, document_name, page_number, author],
            description="Collection of documents Uploaded by the user",
            enable_dynamic_field=True,
        )
        
        collection_name = "temp_collection_" + session_id

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

        collection.insert(milvus_input_data)
        collection.load()

        if utility.has_collection(collection_name):
            status = "Success"
        else:
            status = "Error"
        
        # Record the end time
        end_time = time.time()
        
        # Calculate the elapsed time
        vectorization_time = end_time - start_time
        
        # Prepare the return message
        msg = {
            "message": processed_output, 
            "status": status, 
            "textract_extraction_time": textract_extraction_time, 
            "vectorization_time": vectorization_time
        }
        
        logger.info(f"Total Upload Processing time for uploaded docs: {vectorization_time:.2f} seconds")
        
        return msg
    
    except Exception as e:
        # If an error occurs, raise it
        raise e

def generate_chat_title(userQuestion, AIanswer):
    """
    This function generates a chat title based on the user question and AI answer.
    
    Parameters:
    - userQuestion (str): The user's question.
    - AIanswer (str): The AI's answer.
    
    Returns:
    - title (dict): A dictionary containing the generated chat title.
    """
    messages = [
        {"role": "user", "content": GenerateChatTitlePrompt.format(question=userQuestion, answer=AIanswer)},
    ]
    response = _openai_client.chat_completion_request(messages)
    title = response.choices[0].message.content
    return {"title": title}