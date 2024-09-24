import logging
import tiktoken
import time
from ai_core.openai_prompts import summarySystemPrompt, combineSummaryTemplate, summaryContentPrompt
from pymilvus import connections, Collection
import ai_core.openai_client as _openai_client
from ai_core.langfuse_client import log_and_raise_error
from django.conf import settings
import asyncio
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize tokenizer
tokenizer = tiktoken.get_encoding("cl100k_base")


# create the length function
def tiktoken_len(text):
    tokens = tokenizer.encode(text, disallowed_special=())
    return len(tokens)



def get_summary_chunk(
    chunk,
    summary_objective,
    key_focus_areas,
    desired_length,
    additional_instructions,
    trace_id=None,
    regenerate=False,
):
    try:
        messages = [
            {"role": "system", "content": summarySystemPrompt},
            {
                "role": "user",
                "content": summaryContentPrompt.format(
                    summary_objective=summary_objective,
                    key_focus_areas=str(key_focus_areas),
                    desired_length=desired_length,
                    additional_instructions=additional_instructions,
                    content=chunk,
                ),
            },
        ]
        response, generation_trace = _openai_client.chat_completion_request_stream(
            messages,
            trace_id=trace_id,
            request_name="ChunkSummary",
            temperature=0.3 if regenerate else 0.2,
        )
        return response, generation_trace
    except Exception as e:
        log_and_raise_error(
            f"docSummary -> get_summary_chunk: An error occurred: {e}", trace_id
        )


async def get_summary_chunk_async(
    chunk, summary_objective, key_focus_areas, desired_length, additional_instructions, trace_id=None, regenerate=False
):
    try:
        messages = [
            {"role": "system", "content": summarySystemPrompt},
            {
                "role": "user",
                "content": summaryContentPrompt.format(
                    summary_objective=summary_objective,
                    key_focus_areas=str(key_focus_areas),
                    desired_length=desired_length,
                    additional_instructions=additional_instructions,
                    content=chunk,
                ),
            },
        ]
        response = await _openai_client.chat_completion_request_async(
            messages,
            trace_id=trace_id,
            request_name="ChunkSummary",
            temperature=0.3 if regenerate else 0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        log_and_raise_error(
            f"docSummary -> get_summary_chunk: An error occurred: {e}", trace_id
        )


def getSummary(
    collection_name,
    document_names,
    summary_objective,
    key_focus_areas,
    desired_length,
    additional_instructions,
    trace_id=None,
    regenerate=False,
):
    try:
        text_chunks = []
        text_to_summarize = ""
        chunks_to_summarize = []
        conn = connections.connect(host=settings.MILVUS_HOST,port=settings.MILVUS_PORT, secure=False)

        collection = Collection(collection_name)
        sources = []
        retrival_start_time = time.time()
        for i in range(len(document_names)):
            res = collection.query(
                expr=f"document_name in ['{document_names[i]}']",
                output_fields=["text", "author"],
                consistency_level="Strong",
            )
            chunks = []
            text = "Document Name: " + document_names[i] + "\n\n"
            for doc in res:
                table_pattern_to_skip = r"Table: Table_[1-9]\d*"
                if re.match(table_pattern_to_skip, doc["text"]):
                    continue

                if tiktoken_len(text) + tiktoken_len(doc["text"]) > 75000:
                    chunks.append(text)
                    text = ""
                text += doc["text"]
            if text:
                chunks.append(text)

            source = {
                "id": i + 1,
                "DocumentName": document_names[i],
                "content": "",
                "PageNumber": None,
                "author": res[0]["author"],
                "flag": "Uploaded By You",
            }
            sources.append(source)
            text_chunks.extend(chunks)

        for text_chunk in text_chunks:
            if tiktoken_len(text_to_summarize) + tiktoken_len(text_chunk) > 75000:
                chunks_to_summarize.append(text_to_summarize)
                text_to_summarize = ""
            text_to_summarize += text_chunk
        if text_to_summarize:
            chunks_to_summarize.append(text_to_summarize)
        # if trace_id:
        #     span = langfuse.span(
        #         trace_id=trace_id,
        #         name="documentRetrieval",
        #         start_time=retrival_start_time,
        #         end_time=time.time(),
        #         input=document_names,
        #         output=chunks,
        #         status_message="Success",
        #         metadata={
        #             "collection_name": collection_name,
        #             "document_names": document_names,
        #             "summary_objective": summary_objective,
        #             "key_focus_areas": key_focus_areas,
        #             "desired_length": desired_length,
        #             "additional_instructions": additional_instructions,
        #         },
        #     )
        
        # 

        if len(chunks_to_summarize) > 1:
            chunkSummary = ""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            chunkSummaries = loop.run_until_complete(
                asyncio.gather(
                    *[ 
                        get_summary_chunk_async(
                            chunk,
                            summary_objective,
                            key_focus_areas,
                            desired_length,
                            additional_instructions,
                            trace_id,
                            regenerate=regenerate,
                        )
                        for chunk in chunks_to_summarize
                    ]
                )
            )
            chunkSummary = "\n\n".join(chunkSummaries)
            messages = [
                {
                    "role": "system",
                    "content": combineSummaryTemplate.format(
                        summary_objective=summary_objective,
                        key_focus_areas=str(key_focus_areas),
                        desired_length=desired_length,
                        additional_instructions=additional_instructions,
                    ),
                },
                {"role": "user", "content": chunkSummary},
            ]
            summary_response, generation_trace = (
                _openai_client.chat_completion_request_stream(
                    messages,
                    trace_id=trace_id,
                    request_name="Final Summary",
                    temperature=0.2,
                    max_tokens=4096,
                )
            )
        else:
            summary_response, generation_trace = get_summary_chunk(
                chunks_to_summarize[0],
                summary_objective,
                key_focus_areas,
                desired_length,
                additional_instructions,
                trace_id=trace_id,
                regenerate=regenerate,
            )
        is_stream = True

        return summary_response, sources, is_stream, generation_trace
    except Exception as e:
        log_and_raise_error(
            f"docSummary -> getSummary: An error occurred: {e}", trace_id
        )
