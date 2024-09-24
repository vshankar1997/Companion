import logging
import ai_core.openai_prompts as _prompts
import ai_core.doc_retriever as doc_retriever
import ai_core.image_retriever as image_retriever
from typing import List, Dict, Any, Optional
import ai_core.openai_client as _openai_client
# from ai_core.langfuse_client import langfuse
import gen_ai.settings as settings
import re
import concurrent.futures
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


OpenAIModel = settings.CHAT_MODEL_NAME


def KnowledgeBase(
    collection_name: str,
    image_collection_name: str,
    user_question: str,
    search_queries: List[str],
    preliminary_answer: str,
    answer_depth: str,
    additional_instructions: str,
    get_only_images: bool=False,
    regenerate=False,
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    try:
        images = {}
        retrieved_docs = []

        is_stream=False
        relevant_docs = []
        if get_only_images == False:
            logger.info("Both textual and images are needed.")
            if image_collection_name != None:
                with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
                    logger.info("Image collection name provided, hence both text and images will be retrieved.")
                    start_time = time.time()
                    doc_process = executor.submit(doc_retriever.get_relevant_docs, collection_name, user_question, search_queries, preliminary_answer, answer_depth, trace_id)
                    image_process = executor.submit(image_retriever.get_relevant_images, image_collection_name, user_question, search_queries, preliminary_answer, answer_depth, get_only_images, "None", trace_id)
                    end_time = time.time()
                    logger.info(f"Time taken for both processes (Image and Doc retreivals): {end_time - start_time}")
                    images = image_process.result()
                    retrieved_docs = doc_process.result()
                    logger.info (f"Retrieved Images: {images}")

            else:
                logger.info("No image collection name provided, hence only text will be retrieved.")
                # Get relevant documents
                retrieved_docs = doc_retriever.get_relevant_docs(
                    collection_name=collection_name,
                    user_question=user_question,
                    search_queries=search_queries,
                    preliminary_answer=preliminary_answer,
                    answer_depth=answer_depth,
                    trace_id=trace_id,
                )
        
            if retrieved_docs == []:
                logger.info("No documents retrieved. Hence, returning a generic message.")
                return (
                    "I'm sorry, I couldn't find any relevant information for your question. Please try rephrasing your question or ask something else.",
                    [],
                    [],
                    is_stream,
                    None,
                )
            for i in range(len(retrieved_docs)):
                if retrieved_docs[i]['score'] > 0.25:
                    relevant_docs.append(retrieved_docs[i])
                    
            if len(relevant_docs) == 0:
                logger.info("No relevant documents found. Hence, returning a generic message.")
                return (
                    "I'm sorry, I couldn't find any relevant information for your question. Please try rephrasing your question or ask something else.",
                    [],
                    [],
                    is_stream,
                    None,
                )

            # Construct context string using list comprehension for better performance
            context = "".join(
                [
                    "<source id=[${" +doc['tag']+ "}]>\n{" + doc['content'] + "\n</source>\n\n"
                    for i, doc in enumerate(relevant_docs)
                ]
            )

            # Prepare messages
            messages = [
                {
                    "role": "user",
                    "content": _prompts.qaPromptNew.format(
                        context=context,
                        user_question=user_question,
                        answer_depth=answer_depth,
                        additional_instructions=additional_instructions,
                    ),
                },
            ]
            logger.info(f"Generating Response using open ai")
            # Get chat completion request
            answer_response, generation_trace = _openai_client.chat_completion_request_stream(
                messages,
                trace_id=trace_id,
                request_name="QuestionAnswering",
                model=OpenAIModel,
                temperature=0.3 if regenerate else 0.2,
            )
            is_stream = True
                
            for i in range(len(relevant_docs)):
                updated_source = re.sub("\n\n", "<replaced_text>", relevant_docs[i]['content'])
                updated_source = re.sub("\n", " ", updated_source)
                updated_source = re.sub("<replaced_text>", "\n\n", updated_source)
                relevant_docs[i]['content'] = updated_source
            
            
            chunknumbers =[]
            for source in relevant_docs:
                if int(source['tag'][:-1]) not in chunknumbers:
                    chunknumbers.append(int(source['tag'][:-1]))
                    
            source_references = []
            for chunk in chunknumbers:
                for doc in relevant_docs:
                    if int(doc['tag'][:-1]) == chunk:
                        source = {
                            "ChunkNumber": chunk,
                            "DocumentName": doc["DocumentName"],
                            "author": doc["author"],
                            "flag": "Uploaded By You" if "temp_collection_" in collection_name else "Internal",
                        }
                        source_references.append(source)
                        break
            
            for i in range(len(chunknumbers)):
                content = []
                for doc in relevant_docs:
                    if int(doc['tag'][:-1]) == chunknumbers[i]:
                        content.append(
                            {
                                "tag": doc["tag"],
                                "source": doc["content"],
                                "score": doc["score"],
                                "pageNumber": doc["PageNumber"],
                            }
                        )
                source_references[i]["content"] = content
        else:
            logger.info("Only images are needed.")  
            images = image_retriever.get_relevant_images(
                collection_name=image_collection_name,
                user_question=user_question,
                search_queries=search_queries,
                preliminary_answer=preliminary_answer,
                answer_depth=answer_depth,
                get_only_images=get_only_images,
                trace_id=trace_id,
            )
        
            answer_response = "I have found some images that might be relevant to your question. Please have a look at them below."
            retrieved_docs = []
            generation_trace = None
            is_stream = False
            source_references = []
            images_lst = []
            for key in images:
                images_lst.extend(images[key])

        if images != {}:
            if len(relevant_docs) > 0:
                source_doc_names = [doc['DocumentName'] for doc in relevant_docs]
            else:
                source_doc_names = []
            images_lst = []
            source_images_lst = []
            non_source_images_lst = []
            for key in images:
                if images[key][0]['document_name'] in source_doc_names:
                    source_images_lst.extend(images[key])
                else:
                    non_source_images_lst.extend(images[key])
            images_lst = source_images_lst + non_source_images_lst
        else:
            images_lst = []

        return answer_response, source_references, images_lst, is_stream, generation_trace

    except Exception as e:
        logger.error(f"QA_tools -> KnowledgeBase: Error Occured During Tool call {e}")
        logger.error(f"Exception: {e}")
        raise e
