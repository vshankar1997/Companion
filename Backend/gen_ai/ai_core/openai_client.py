from openai import OpenAI, AsyncOpenAI
import tiktoken
import time
import logging
from ai_core.langfuse_client import log_and_raise_error
import ai_core.openai_prompts as _prompts
import gen_ai.settings as settings



# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

async_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Initialize tokenizer
tokenizer = tiktoken.get_encoding("cl100k_base")

def embedding_request(text, trace_id=None, request_name="embedding_request"):
    """Request embedding from OpenAI"""
    try:
        response = (
            client.embeddings.create(
                input=text, model=settings.EMBEDDING_MODEL_NAME
            )
            .data[0]
            .embedding
        )
        # if trace_id is not None:
        #     trace = langfuse.trace(id=trace_id)
        #     trace.generation(
        #         name=request_name,
        #         model=settings.EMBEDDING_MODEL_NAME,
        #         input=text,
        #         output=response,
        #         status_message="Success",
        #     )
        return response
    except Exception as e:
        log_and_raise_error(
            f"OpenAI Client -> embedding_request: Failed to create embedding: {e}",
            trace_id,
        )
        raise e


def chat_completion_request(
    messages,
    tools=None,
    tool_choice=None,
    model=settings.CHAT_MODEL_NAME,
    trace_id=None,
    request_name="chat_completion_request",
    temperature=0.2,
    max_tokens=4095,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    stop="",
    stream=False,
):
    """Request chat completion from OpenAI"""
    params = {
        "model": model,
        "temperature": temperature,
        "messages": messages,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty,
        "stop": stop,
        "stream": stream,
    }

    if tools is not None:
        params["tools"] = tools
        if tool_choice is not None:
            params["tool_choice"] = tool_choice

    try:
        start_time = time.time()
        response = client.chat.completions.create(**params)
        end_time = time.time()
        elapsed_time = end_time - start_time
        response.time_taken = elapsed_time
        if response.choices[0].finish_reason == "tool_calls":
            output_message = response.choices[0].message.tool_calls
        elif response.choices[0].finish_reason == "stop":
            output_message = response.choices[0].message.content
        elif response.choices[0].finish_reason == "length":
            partialResponse = response.choices[0].message.content
            messages.append(
                {
                    "role": "user",
                    "content": _prompts.longResponsePrompt.format(
                        response=partialResponse
                    ),
                }
            )
            response = client.chat.completions.create(**params)
            end_time = time.time()
            elapsed_time = end_time - start_time
            response.time_taken = elapsed_time
            output_message = partialResponse + response.choices[0].message.content
        # if trace_id is not None:
        #     trace = langfuse.trace(id=trace_id)
        #     trace.generation(
        #         name=request_name,
        #         model=model,
        #         model_parameters={
        #             "maxTokens": max_tokens,
        #             "temperature": temperature,
        #             "topP": top_p,
        #             "frequencyPenalty": frequency_penalty,
        #             "presencePenalty": presence_penalty,
        #             "stop": stop,
        #             "stream": stream,
        #             "tool_choice": tool_choice if tool_choice is not None else "auto",
        #         },
        #         input=messages,
        #         metadata={
        #             "tools": tools,
        #         },
        #         output=output_message,
        #         start_time=start_time,
        #         end_time=end_time,
        #         status_message="Success",
        #         usage=response.usage,
        #     )

        return response
    except Exception as e:
        log_and_raise_error(
            f"OpenAI Client -> chat_completion_request: An error occurred: {e}  + {response if 'response' in locals() else ''}",
            trace_id,
        )


async def chat_completion_request_async(
    messages,
    tools=None,
    tool_choice=None,
    model=settings.CHAT_MODEL_NAME,
    trace_id=None,
    request_name="chat_completion_request",
    temperature=0.2,
    max_tokens=4095,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    stop="",
    stream=False,
):
    """Request chat completion from OpenAI"""
    params = {
        "model": model,
        "temperature": temperature,
        "messages": messages,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty,
        "stop": stop,
        "stream": stream,
    }

    if tools is not None:
        params["tools"] = tools
        if tool_choice is not None:
            params["tool_choice"] = tool_choice

    try:
        start_time = time.time()
        response = await async_client.chat.completions.create(**params)
        end_time = time.time()
        elapsed_time = end_time - start_time
        response.time_taken = elapsed_time
        if response.choices[0].finish_reason == "tool_calls":
            output_message = response.choices[0].message.tool_calls
        elif response.choices[0].finish_reason == "stop":
            output_message = response.choices[0].message.content
        elif response.choices[0].finish_reason == "length":
            partialResponse = response.choices[0].message.content
            messages.append(
                {
                    "role": "user",
                    "content": _prompts.longResponsePrompt.format(
                        response=partialResponse
                    ),
                }
            )
            response = await async_client.chat.completions.create(**params)
            end_time = time.time()
            elapsed_time = end_time - start_time
            response.time_taken = elapsed_time
            output_message = partialResponse + response.choices[0].message.content
        # if trace_id is not None:
        #     trace = langfuse.trace(id=trace_id)
        #     trace.generation(
        #         name=request_name,
        #         model=model,
        #         model_parameters={
        #             "maxTokens": max_tokens,
        #             "temperature": temperature,
        #             "topP": top_p,
        #             "frequencyPenalty": frequency_penalty,
        #             "presencePenalty": presence_penalty,
        #             "stop": stop,
        #             "stream": stream,
        #             "tool_choice": tool_choice if tool_choice is not None else "auto",
        #         },
        #         input=messages,
        #         metadata={
        #             "tools": tools,
        #         },
        #         output=output_message,
        #         start_time=start_time,
        #         end_time=end_time,
        #         status_message="Success",
        #         usage=response.usage,
        #     )

        return response
    except Exception as e:
        log_and_raise_error(
            f"OpenAI Client -> chat_completion_request: An error occurred: {e}  + {response if 'response' in locals() else ''}",
            trace_id,
        )
        
        


def chat_completion_request_stream(
    messages,
    tools=None,
    tool_choice=None,
    model=settings.CHAT_MODEL_NAME,
    trace_id=None,
    request_name="chat_completion_request_stream",
    temperature=0.2,
    max_tokens=4095,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    stop="",
    stream=True,
):
    """Request chat completion from OpenAI"""
    params = {
        "model": model,
        "temperature": temperature,
        "messages": messages,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty,
        "stop": stop,
        "stream": stream,
    }

    if tools is not None:
        params["tools"] = tools
        if tool_choice is not None:
            params["tool_choice"] = tool_choice

    try:
        start_time = time.time()
        response = client.chat.completions.create(**params)
        # if trace_id is not None:
        #     trace = langfuse.trace(id=trace_id)
        #     generation_trace = trace.generation(
        #         name=request_name,
        #         model=model,
        #         model_parameters={
        #             "maxTokens": max_tokens,
        #             "temperature": temperature,
        #             "topP": top_p,
        #             "frequencyPenalty": frequency_penalty,
        #             "presencePenalty": presence_penalty,
        #             "stop": stop,
        #             "stream": stream,
        #             "tool_choice": tool_choice if tool_choice is not None else "auto",
        #         },
        #         input=messages,
        #         metadata={
        #             "tools": tools,
        #         },
        #         start_time=start_time,
        #         status_message="Processing...",
        #     )
        # else:
        #     generation_trace = None
        generation_trace = None
        return response, generation_trace
    except Exception as e:
        log_and_raise_error(
            f"OpenAI Client -> chat_completion_request: An error occurred: {e}  + {response if 'response' in locals() else ''}",
            trace_id,
        )
