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
def create_search_images_and_rerank(
    query_results, user_question, answer_depth, get_only_images, trace_id=None
):
    try:
        searchDocuments = []
        # start_time_reranker = time.time()
        for queryResult in query_results:
            searchDocument = {
                "id": queryResult["id"],
                "text": queryResult["Image_Text"],
                "metadata": {
                    "PDF_Name": queryResult["PDF_Name"],
                    "image_path": queryResult["image_path"],
                    "Page_Number": queryResult["Page_Number"],
                    "Image_Number": queryResult["Image_Number"],
                    "img_id": queryResult["img_id"],
                    "Title": queryResult["Title"],
                    "Caption": queryResult["Caption"],
                    "pdf_path": queryResult["pdf_path"]
                },
            }
            searchDocuments.append(searchDocument)
        rerankrequest = RerankRequest(query=user_question, passages=searchDocuments)
        noOfContextImages = (
            6
            if answer_depth == "High"
            else 6 if answer_depth == "Medium" else 4 if answer_depth == "Low" else 4
        )

        Image_Threshold = 85
        if get_only_images == True:
            min_num_images = 2
        
        reRankedDocuments = ranker.rerank(rerankrequest)[:noOfContextImages]
        logger.info("Image Rerank scores")
        for idx, r in enumerate(reRankedDocuments):
            logger.info(f"Image Rerank: {r['score']}")
            
        reRankedDocuments_log = [
            {
            "img_id": r["id"],
            # "text": r["text"],
            'path': r['metadata']['image_path'],
            "title": r['metadata']['Title'],
            "caption": r['metadata']['Caption'],
            "document_name": r['metadata']['PDF_Name'],
            "pdf_path": r['metadata']['pdf_path'],
            "page_number": r['metadata']['Page_Number'],            
            "relevance_score": float(r["score"]),
            }
            for idx, r in enumerate(reRankedDocuments)
            if round(r['score']*100, 2) > Image_Threshold
        ]
        
        if get_only_images == True :
            min_num_images = 2
            if len(reRankedDocuments_log) < min_num_images:
                reRankedDocuments_log = [
                    {
                    "img_id": r["id"],
                    # "text": r["text"],
                    'path': r['metadata']['image_path'],
                    "title": r['metadata']['Title'],
                    "caption": r['metadata']['Caption'],
                    "document_name": r['metadata']['PDF_Name'],
                    "pdf_path": r['metadata']['pdf_path'],
                    "page_number": r['metadata']['Page_Number'],            
                    "relevance_score": float(r["score"]),
                    }
                    for idx, r in enumerate(reRankedDocuments[:2])
                ]

        grouped_ranked_documents = {}
        for image_dict in reRankedDocuments_log:
            document_name = image_dict["document_name"]
            grouped_ranked_documents.setdefault(document_name, []).append(image_dict)
        
        logger.info(f"Grouped ranked documents: {grouped_ranked_documents}")
        # if trace_id is not None:
        #     span = langfuse.span(
        #         trace_id=trace_id,
        #         name="FlashRank Image Reranking",
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
        return grouped_ranked_documents
    except Exception as e:
        log_and_raise_error(
            f"ImageRetriever -> create_search_images_and_rerank: Failed to create search documents and rerank: {e}"
            # trace_id=trace_id,
        )


def get_relevant_images(
    collection_name: str,
    user_question: str,
    search_queries: List[str],
    preliminary_answer: str,
    answer_depth: str,
    get_only_images : bool,
    qa_response: Optional[str] = None,
    trace_id: Optional[str] = None,
):
    try:
        if qa_response is not None:
            semanticSearchQuery = "QUESTION: \n" + user_question + "\n\n ANSWER: \n" + qa_response
        else:
            semanticSearchQuery = (
            user_question
            + "\n"
            + ", \n".join(search_queries)
            + "\n\n "
            + preliminary_answer
            )
        # start_time_retrieval = time.time()
        conn = connections.connect(host=settings.MILVUS_HOST,port=settings.MILVUS_PORT, secure=False)
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
                20
                if answer_depth == "High"
                else 15 if answer_depth == "Medium" else 10 if answer_depth == "Low" else 10
            ),
            expr=None,
            output_fields=[
                "image_path",
                "Image_Text",
                "PDF_Name",
                "Page_Number",
                "Image_Number",
                "img_id",
                "Title",
                "Caption",
                'pdf_path'
            ],
            consistency_level="Strong",
        )
        query_results = [
            {
                "id": query_results.id,
                "distance": query_results.distance,
                "image_path": query_results.image_path,
                "Image_Text": query_results.Image_Text,
                "PDF_Name": query_results.PDF_Name,
                "Page_Number": query_results.Page_Number,
                "Image_Number": query_results.Image_Number,
                "img_id": query_results.img_id,
                "Title": query_results.Title,
                "Caption": query_results.Caption,
                "pdf_path": query_results.pdf_path,
            }
            for idx, query_results in enumerate(results[0])
        ]

        # if trace_id is not None:
        #     span = langfuse.span(
        #         trace_id=trace_id,
        #         name="Milvus Image Retrieval",
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
        reRankedDocuments_log = create_search_images_and_rerank(
            query_results,
            user_question,
            answer_depth,
            get_only_images,
            trace_id=trace_id,
        )
        return reRankedDocuments_log
        # return searchDocuments
    except Exception as e:
        log_and_raise_error(f"Failed to retrieve relevant docs: {e}", trace_id=trace_id)