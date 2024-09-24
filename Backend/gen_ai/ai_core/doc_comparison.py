import logging
from numpy import add
from typing import List, Dict, Any, Optional
from ai_core.langfuse_client import log_and_raise_error
import time
from pymilvus import connections, Collection
import tiktoken
from django.conf import settings

import ai_core.openai_prompts as _prompts
import ai_core.openai_client as _openai_client

# Set up logging
logger = logging.getLogger(__name__)

def tiktoken_len(text):
    """
    Tokenize the input text using a specified tokenizer and return the number of tokens.

    :param text: Input text to be tokenized.
    :return: Number of tokens in the tokenized text.
    """
    try:
        # Tokenize the text using the specified tokenizer
        tokenizer = tiktoken.get_encoding('cl100k_base')
        tokens = tokenizer.encode(
            text,
            disallowed_special=()
        )
        return len(tokens)
        
    except Exception as e:
        raise(e)  

def get_docs_for_comparison(
    collection_name: str,
    document_names: List[str],
    trace_id: Optional[str] = None,
):
    """
    Retrieve relevant documents for comparison.

    :param collection_name: Name of the collection.
    :param document_names: List of document names to retrieve.
    :param trace_id: Optional trace ID for logging and error handling.
    :return: List of query results containing relevant documents.
    """
    try:
        logger.info("QA_tools -> CompareDocuments: Retrieving relevant documents")
        # start_time_retrieval = time.time()
        conn = connections.connect(host=settings.MILVUS_HOST,port=settings.MILVUS_PORT,secure=False)

        collection = Collection(collection_name)
        collection.load()

        query_results = []

        for i in range(len(document_names)):
            results = collection.query(
                expr=f"document_name in ['{document_names[i]}']",
                output_fields=[
                    "chunk_id",
                    "text",
                    "document_name",
                    "page_number",
                    "author",
                ],
                consistency_level="Strong",
                limit=16384,
            )

            seen_texts = set()
            unique_query_results = []

            for idx, query_result in enumerate(results):
                if query_result["text"] not in seen_texts:
                    seen_texts.add(query_result["text"])
                    unique_query_results.append(
                        {
                            "chunk_id": query_result["chunk_id"],
                            "text": query_result["text"],
                            "author": query_result["author"],
                            "document_name": query_result["document_name"],
                            "page_number": query_result["page_number"],
                        }
                    )
                else:
                    logger.info(f"chunk_id missed : {query_result['chunk_id']}")
                    logger.info(f"text: {query_result['text']}")

            logger.info(f"unique_query_results : {unique_query_results}")
            query_results.append(unique_query_results)

        # if trace_id:
        #     langfuse.span(
        #         trace_id=trace_id,
        #         name="Milvus Data Retrieval",
        #         start_time=start_time_retrieval,
        #         end_time=time.time(),
        #         input=str(document_names),
        #         output=query_results,
        #         status_message="Success",
        #         metadata={
        #             "collection": collection_name,
        #             "limit": 16384,
        #             "document_names": document_names,
        #         },
        #     )
        return query_results
    except Exception as e:
        log_and_raise_error(
            f"get_docs_for_comparison: Failed to retrieve relevant docs: {e}",
            trace_id=trace_id,
        )

def getComparison(
    collection_name: str,
    document_names: List[str],
    key_focus_areas: Optional[List[str]],
    regenerate: bool = False,
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compare documents and generate a comparison using OpenAI.

    :param collection_name: Name of the collection.
    :param document_names: List of document names to compare.
    :param key_focus_areas: Optional list of key focus areas for the comparison.
    :param regenerate: Flag indicating whether to regenerate the comparison.
    :param trace_id: Optional trace ID for logging and error handling.
    :return: Dictionary containing the comparison result, source references, stream flag, and generation trace.
    """
    try:
        logger.info("QA_tools -> CompareDocuments: Comparing documents")
        is_stream = False
        # Get relevant documents
        retrieved_docs = get_docs_for_comparison(
            collection_name=collection_name,
            document_names=document_names,
            trace_id=trace_id,
        )

        if retrieved_docs == []:
            return (
                "I'm sorry, I couldn't find any relevant information for your query. Please try rephrasing your question or ask something else.",
                [],
                None,
                is_stream,
            )

        # Prepare documents
        document_1 = ""
        for doc in retrieved_docs[0]:
            document_1 += doc["text"]
        document_2 = ""
        for doc in retrieved_docs[1]:
            document_2 += doc["text"]

        # Get the number of tokens in each document
        doc1_tokens = tiktoken_len(document_1)
        logger.info(f"Number of tokens in document 1: {doc1_tokens}")
        doc2_tokens = tiktoken_len(document_2)
        logger.info(f"Number of tokens in document 2: {doc2_tokens}")
        # Check if the number of tokens in the documents exceed the limit
        each_doc_token_limit = 40000
        if doc1_tokens > each_doc_token_limit or doc2_tokens > each_doc_token_limit:
            is_stream = False
            if doc1_tokens > each_doc_token_limit and doc2_tokens > each_doc_token_limit:
                return ("I'm sorry, documents are too long to compare. Please try comparing shorter documents.",
                [],
                None,
                is_stream)
            elif doc1_tokens > each_doc_token_limit:
                return (f"I'm sorry, the document '{document_names[0]}' is too long to compare. Please try comparing a shorter document.",
                [],
                None,
                is_stream)
            else:
                return (
                f"I'm sorry, the document '{document_names[1]}' is too long to compare. Please try comparing a shorter document.",
                [],
                None,
                is_stream)
        
        if key_focus_areas is not None:
            instructions = _prompts.ComparisonInstructions.format(
                key_focus_areas=key_focus_areas
            )
        else:
            instructions = ""
        # Prepare messages
        messages = [
            {
                "role": "user",
                "content": _prompts.ComparisonPrompt.format(
                    document_1=document_1,
                    document_2=document_2,
                    document_1_name=document_names[0],
                    document_2_name=document_names[1],
                    comparison_instructions=instructions,
                ),
            },
        ]
        logger.info(f"Generating Comparison using open ai")
        logger.info(f"Messages: {messages}")
        # Get chat completion request
        answer_response, generation_trace = (
            _openai_client.chat_completion_request_stream(
                messages,
                trace_id=trace_id,
                request_name="CompareDocuments",
                temperature=0.5 if regenerate else 0.2,
            )
        )
        is_stream = True
        try:
            source_references = []
            for idx, doc in enumerate(retrieved_docs):
                doc_sources = {
                    "id": idx+1,
                    "DocumentName": doc[0]["document_name"],
                    "flag" : "Uploaded By You",
                    "content": "",
                    "PageNumber": None,
                    "author": doc[0]["author"],
                }
                source_references.append(doc_sources)

            return answer_response, source_references, is_stream, generation_trace
        except Exception as e:
            return answer_response, [], is_stream, generation_trace

    except Exception as e:
        logger.error(
            f"QA_tools -> CompareDocuments: Error Occurred During Tool call {e}"
        )
        logger.error(f"Exception: {e}")
        raise e
