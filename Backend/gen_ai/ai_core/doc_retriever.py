import os
# from tenacity import retry, wait_random_exponential, stop_after_attempt
import logging
from flashrank.Ranker import Ranker, RerankRequest
from pymilvus import connections, Collection
from django.conf import settings
import time
from ai_core.langfuse_client import log_and_raise_error
import ai_core.openai_client as _openai_client
from typing import List, Optional
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define retry strategy
# retry_strategy = retry(
#     wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3)
# )

# Initialize Milvus client
conn = connections.connect(host=settings.MILVUS_HOST,port=settings.MILVUS_PORT, secure=False)

# Initialize Flash Rank
ranker = Ranker(model_name=settings.RANKER_MODEL_NAME)

# @retry_strategy
def create_search_documents_and_rerank(
    query_results, user_question, answer_depth, trace_id=None
):
    """
    Create search documents and rerank the results based on the user's question and answer depth.
    Args:
        query_results (list): A list of query results.
        user_question (str): The user's question.
        answer_depth (str): The desired depth of the answer. Can be "High", "Medium", or "Low".
        trace_id (str, optional): The trace ID. Defaults to None.
    Returns:
        list: A list of relevant documents with their metadata, content, and scores.
    """
    try:
        searchDocuments = []
        for queryResult in query_results:
            searchDocument = {
                "id": queryResult["id"],
                "text": queryResult["text"],
                "metadata": {
                    "author": queryResult["author"],
                    "document_name": queryResult["document_name"],
                    "page_number": queryResult["page_number"],
                    # "chunk_id": queryResult["chunk_id"],
                },
            }
            searchDocuments.append(searchDocument)
        rerankrequest = RerankRequest(query=user_question, passages=searchDocuments)
        noOfContextDocuments = (
            10
            if answer_depth == "High"
            else 7 if answer_depth == "Medium" else 5 if answer_depth == "Low" else 5
        )
        reRankedDocuments = ranker.rerank(rerankrequest)[:noOfContextDocuments]
        reRankedDocuments_log = [
            {
                "id": r["id"],
                "text": r["text"],
                "metadata": r["metadata"],
                "score": float(r["score"]),
            }
            for idx, r in enumerate(reRankedDocuments)
        ]
        relevent_docs = []
        for doc in reRankedDocuments_log:
            source = {
                    "id": doc["id"],
                    "DocumentName": doc["metadata"]['document_name'],
                    "content": doc['text'],
                    "PageNumber": doc["metadata"]['page_number'],
                    "author": doc["metadata"]['author'],
                    "score": doc["score"],
                }
            relevent_docs.append(source)
            
        # Initialize a dictionary to track the order and count of each document
        document_order = {}
        document_labels = {}
        order_counter = 1

        # Loop through each document to establish order and count occurrences
        for r in relevent_docs:
            document_name = r["DocumentName"]
            if document_name not in document_order:
                document_order[document_name] = {
                    "order": order_counter,
                    "count": 0,
                }  # Start count from 0
                order_counter += 1

        # Generate labels based on the established order and occurrence count
        for r in relevent_docs:
            document_name = r["DocumentName"]
            order_info = document_order[document_name]
            order_info["count"] += 1  # Increment count for each occurrence
            # Use count for lettering, starting with 'a' for the first occurrence
            label = f"{order_info['order']}{chr(96 + order_info['count'])}"

            document_labels[r["id"]] = label

        # Assign the generated label to each document in reRankedDocuments_log
        for doc_log in relevent_docs:
            doc_id = doc_log["id"]
            label = document_labels[doc_id]
            doc_log["tag"] = label
        
        # if trace_id is not None:
        #     span = langfuse.span(
        #         trace_id=trace_id,
        #         name="FlashRank Reranking",
        #         start_time=start_time_reranker,
        #         end_time=time.time(),
        #         input=user_question,
        #         output=reRankedDocuments_log,
        #         status_message="Success",
        #         metadata={
        #             "reRank_model": "ms-marco-MiniLM-L-12-v2",
        #             "reRank_limit": noOfContextDocuments,
        #         },
        #     )
        return relevent_docs
    except Exception as e:
        log_and_raise_error(
            f"docRetriever -> create_search_documents_and_rerank: Failed to create search documents and rerank: {e}"
            # trace_id=trace_id,
        )


# @retry_strategy
def get_relevant_docs(
    collection_name: str,
    user_question: str,
    search_queries: List[str],
    preliminary_answer: str,
    answer_depth: str,
    trace_id: Optional[str] = None,
):
    """
        Retrieves relevant documents based on the user's question and search queries.
        Args:
            collection_name (str): The name of the collection to search in.
            user_question (str): The user's question.
            search_queries (List[str]): The search queries to include in the semantic search.
            preliminary_answer (str): The preliminary answer to include in the semantic search.
            answer_depth (str): The depth of the answer. Can be "High", "Medium", "Low", or "None".
            trace_id (Optional[str], optional): The trace ID for logging purposes. Defaults to None.
        Returns:
            List[Dict[str, Union[int, float, str]]]: A list of relevant documents with their details, including ID, distance, text, author, document name, and page number.
        Raises:
            Exception: If an error occurs during the retrieval process.
        """
    try:
        semanticSearchQuery = (
            user_question
            + "\n"
            + ", \n".join(search_queries)
            + "\n\n "
            + preliminary_answer
        )
        start_time_retrieval = time.time()
        conn = connections.connect(host=settings.MILVUS_HOST, port=settings.MILVUS_PORT, secure=False)
        collection = Collection(collection_name)
        search_params = {
            "metric_type": "L2",
            "offset": 0,
            "ignore_growing": False,
            "params": {"nprobe": 15},
        }
        results = collection.search(
            data=[
                _openai_client.embedding_request(semanticSearchQuery, trace_id=trace_id)
            ],
            anns_field="vector",
            param=search_params,
            limit=(
                30
                if answer_depth == "High"
                else 20 if answer_depth == "Medium" else 15 if answer_depth == "Low" else 10
            ),
            expr=None,
            output_fields=[
                "text",
                "author",
                "document_name",
                "page_number",
            ],
            consistency_level="Strong",
        )
        query_results = [
            {
                "id": query_results.id,
                "distance": query_results.distance,
                "text": query_results.text,
                "author": query_results.author,
                "document_name": query_results.document_name,
                "page_number": query_results.page_number,
            }
            for idx, query_results in enumerate(results[0])
        ]
        
        # if trace_id is not None:
        #     span = langfuse.span(
        #         trace_id=trace_id,
        #         name="Milvus Data Retrieval",
        #         start_time=start_time_retrieval,
        #         end_time=time.time(),
        #         input=semanticSearchQuery,
        #         output=query_results,
        #         status_message="Success",
        #         metadata={
        #             "collection": collection_name,
        #             "limit": 20,
        #         },
        #     )
        
        reRankedDocuments_log = create_search_documents_and_rerank(
            query_results,
            user_question,
            answer_depth,
            trace_id=trace_id,
        )
        logger.info(f"Number of Retrieved Documents: {len(reRankedDocuments_log)}")
        return reRankedDocuments_log        
    except Exception as e:
        log_and_raise_error(f"docRetriever -> get_relevant_docs: Error Occured: {e}", trace_id=trace_id)
