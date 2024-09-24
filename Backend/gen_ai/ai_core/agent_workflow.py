import json
import logging
from ai_core.openai_tools import tools, upload_tools
import time
from ai_core.langfuse_client import log_and_raise_error
from ai_core.conversation_memory import Conversation
import ai_core.openai_prompts as _prompts
import ai_core.openai_client as _openai_client
import ai_core.QA_tools as _QA_tools
import ai_core.doc_summary as _docSummary
import ai_core.doc_comparison as _docComparison

# Set up logging
logger = logging.getLogger(__name__)


def process_responses(responses, generation_trace):
    """
    Process responses and extract tool calls information
    """
    tool_calls_info = []
    current_tool_call_arguments = ""
    current_index = -1

    for response_chunk in responses:
        choice = response_chunk.choices[0]
        delta = choice.delta

        # Return the streaming object if delta.content is not None
        if delta.content is not None:
            return responses, generation_trace, False

        # Process tool calls
        if delta.tool_calls:
            tool_call = delta.tool_calls[0]
            tool_call_index = tool_call.index
            tool_call_name = tool_call.function.name
            tool_call_arguments = tool_call.function.arguments

            # When a new tool call is encountered
            if tool_call_index > current_index:
                # Save the previous tool call if any
                if current_index >= 0:
                    tool_calls_info.append(
                        (function_name, json.loads(current_tool_call_arguments))
                    )
                    current_tool_call_arguments = ""

                current_index = tool_call_index
                function_name = tool_call_name

            # Accumulate arguments
            current_tool_call_arguments += tool_call_arguments

    # After the loop, add the last tool call's information
    if current_index >= 0:
        tool_calls_info.append((function_name, json.loads(current_tool_call_arguments)))

    if generation_trace:
        generation_trace.update(
            output=tool_calls_info,
            status_message="Success",
            end_time=time.time(),
        )
    return tool_calls_info, generation_trace, True


def handle_QA_tool_calls(
    function_name,
    function_arguments,
    collection_name,
    uploaded_collection_name=None,
    trace_id=None,
    regenerate=False,
):
    """
    Handles QA tool calls and returns the function name, user question, answer, and sources
    """
    try:
        user_question = function_arguments.get("user_question", "")
        search_queries = function_arguments.get("search_queries", [])
        preliminary_answer = function_arguments.get("preliminary_answer", "")
        answer_depth = function_arguments.get("answer_depth", "")
        additional_instructions = function_arguments.get("additional_instructions", "")
        get_only_images = function_arguments.get("show_only_images", False)
        logger.info(f"QA Tool Called -> Function Name: {function_name}")
        if function_name == "KnowledgeBaseAssistant":
            image_collection_name = collection_name + "_IMAGES"
            logger.info(f"Image Collection Name: {image_collection_name}")
        else:
            image_collection_name = None
        if function_name in [
            "KnowledgeBaseAssistant",
            "InternalKnowledgeBase",
            "UploadedKnowledgeBase",
        ]:
            answer_response, answer_sources, images, is_stream, generation_trace = (
                _QA_tools.KnowledgeBase(
                    collection_name=(
                        collection_name
                        if function_name != "UploadedKnowledgeBase"
                        else uploaded_collection_name
                    ),
                    image_collection_name=image_collection_name,
                    user_question=user_question,
                    search_queries=search_queries,
                    preliminary_answer=preliminary_answer,
                    answer_depth=answer_depth,
                    additional_instructions=additional_instructions,
                    get_only_images=get_only_images,
                    regenerate=regenerate,
                    trace_id=trace_id,
                )
            )
        return answer_response, answer_sources, images, get_only_images, is_stream, generation_trace
    except Exception as e:
        log_and_raise_error(
            f"AgentWorkflow -> handle_QA_tool_calls: An error occurred: {e}", trace_id
        )


def handle_summary_tool_calls(
    function_name,
    function_arguments,
    uploaded_collection_name,
    trace_id=None,
    regenerate=False,
):
    """
    Handles summary tool calls and returns the function name, user question, answer, and sources
    """
    try:
        document_names = function_arguments.get("document_names", [])
        summary_objective = function_arguments.get("summary_objective", "")
        key_focus_areas = function_arguments.get("key_focus_areas", [])
        desired_length = function_arguments.get("desired_length", "")
        additional_instructions = function_arguments.get("additional_instructions", "")
        if function_name == "SummarizeUploadedDocuments":
            summary_response, sources, is_stream, generation_trace = (
                _docSummary.getSummary(
                    collection_name=uploaded_collection_name,
                    document_names=document_names,
                    summary_objective=summary_objective,
                    key_focus_areas=key_focus_areas,
                    desired_length=desired_length,
                    additional_instructions=additional_instructions,
                    trace_id=trace_id,
                    regenerate=regenerate,
                )
            )
            return summary_response, sources, is_stream, generation_trace
        else:
            log_and_raise_error(
                f"AgentWorkflow -> handle_summary_tool_calls: Tool Not Defined -> name: {function_name}, arguments: {function_arguments}",
                trace_id,
            )
    except Exception as e:
        log_and_raise_error(
            f"AgentWorkflow -> handle_summary_tool_calls: An error occurred: {e}",
            trace_id,
        )


def handle_comparison_tool_calls(
    function_name,
    function_arguments,
    uploaded_collection_name,
    regenerate=False,
    trace_id=None,
):
    """
    Handles comparison tool calls and returns the comparison by calling the comparison tool
    """
    print(
        f"handle_comparison_tool_calls: Comparing documents {function_arguments} from collection {uploaded_collection_name}"
    )
    try:
        document_names = [
            function_arguments.get("document_name_1", str),
            function_arguments.get("document_name_2", str),
        ]
        key_focus_areas = function_arguments.get("comparison_areas", [])
        if function_name == "ComparingDocumentsAssistant":
            summary_response, sources, is_stream, generation_trace = (
                _docComparison.getComparison(
                    collection_name=uploaded_collection_name,
                    document_names=document_names,
                    key_focus_areas=key_focus_areas,
                    regenerate=regenerate,
                    trace_id=trace_id,
                )
            )
            return summary_response, sources, [], is_stream, generation_trace
        else:
            log_and_raise_error(
                f"AgentWorkflow -> handle_comparison_tool_calls: Tool Not Defined -> name: {function_name}, arguments: {function_arguments}",
                trace_id,
            )
    except Exception as e:
        log_and_raise_error(
            f"AgentWorkflow -> handle_comparison_tool_calls: An error occurred: {e}",
            trace_id,
        )


def tool_action_execution(
    tool_call_info,
    collection_name,
    uploaded_collection_name=None,
    trace_id=None,
    regenerate=False,
):
    """
    Main function execution loop
    """
    try:
        is_stream = False
        get_only_images = False
        images = []
        logger.info(f"Tool Call Info: {tool_call_info}")

        for function_name, function_arguments in tool_call_info:

            if function_name == "SummarizeUploadedDocuments":
                logger.info(f"SummarizeUploadedDocuments Tool called.")
                summary_response, sources, is_stream, generation_trace = (
                    handle_summary_tool_calls(
                        function_name,
                        function_arguments,
                        uploaded_collection_name=uploaded_collection_name,
                        trace_id=trace_id,
                        regenerate=regenerate,
                    )
                )
                return summary_response, sources, images, get_only_images, is_stream, generation_trace
            elif function_name in [
                "KnowledgeBaseAssistant",
                "InternalKnowledgeBase",
                "UploadedKnowledgeBase",
            ]:
                logger.info(f"KnowledgeBase Tool called.")
                answer_response, answer_sources, images, get_only_images, is_stream, generation_trace = (
                    handle_QA_tool_calls(
                        function_name,
                        function_arguments,
                        collection_name,
                        uploaded_collection_name=uploaded_collection_name,
                        trace_id=trace_id,
                        regenerate=regenerate,
                    )
                )
                return answer_response, answer_sources, images, get_only_images, is_stream, generation_trace
            elif function_name == "ComparingDocumentsAssistant":
                comparison_response, sources, images, is_stream, generation_trace = (
                    handle_comparison_tool_calls(
                        function_name,
                        function_arguments,
                        uploaded_collection_name=uploaded_collection_name,
                        regenerate=regenerate,
                        trace_id=trace_id,
                    )
                )
                return comparison_response, sources, images, get_only_images, is_stream, generation_trace
            else:
                tool_name = function_name
                tool_arguments = function_arguments
                log_and_raise_error(
                    f"AgentWorkflow -> tool_action_execution: Tool Not Defined -> name: {tool_name}, arguments: {tool_arguments}",
                    trace_id,
                )
                return None, [], is_stream, images, get_only_images, generation_trace
    except Exception as e:
        log_and_raise_error(
            f"AgentWorkflow -> tool_action_execution: An error occurred: {e}",
            trace_id,
        )


def get_knowledge_response(
    prompt, chat, BU_Name, regenerate, session_id, is_upload, upload_documents
):
    """
    Get knowledge response
    """
    try:
        is_stream = False
        get_only_images = False
        images = []
        conversation = Conversation()
        conversation.start_conversation()

        if is_upload:
            systemMessageInfo = ""
            uploaded_collection_name = "temp_collection_" + session_id
            systemMessageInfo = (
                "\n\n Note: the user has uploaded the following Documents: \n"
            )
            for i in range(len(upload_documents)):
                systemMessageInfo += str(i) + ": " + upload_documents[i] + "\n"

            system_message = _prompts.systemMessage.format(upload_assistants=_prompts.uploadAssistants) + systemMessageInfo
        else:
            uploaded_collection_name = None
            system_message = _prompts.systemMessage.format(upload_assistants="")

        conversation.add_message(
            role="system", content=system_message
        )
        for msg in chat:
            if msg['role'] == 'user':
                conversation.add_message(role=msg["role"], content=msg["content"])
            elif msg['role'] == 'AI':
                conversation.add_message(role="assistant", content=msg["content"])

        conversation.add_message(role="user", content=prompt)

        agent_tools = upload_tools if uploaded_collection_name else tools

        # trace = langfuse.trace(
        #     name="hzn-companion-paln-and-execute-agent",
        #     input=conversation.conversation_history[-1]["content"],
        #     start_time=time.time(),
        #     session_id=session_id,
        #     user_id=user_id,
        #     tags=["development"],
        #     public=False,
        # )
        # trace_id = trace.id
        trace_id = None
        trace = None
        generation_trace = None

        full_message_response, generation_trace = _openai_client.chat_completion_request_stream(
            conversation.conversation_history,
            tools=agent_tools,
            trace_id=trace_id,
            request_name="PlanAndExecuteAgent",
            temperature=0.3 if regenerate else 0.2,
        )
        processed_output, generation_trace, is_tool_call = process_responses(
            full_message_response, generation_trace
        )

        logger.info(f"Did a tool call (YES/NO): {is_tool_call}")

        if not is_tool_call:
            is_stream = True
            return processed_output, [], images, get_only_images, is_stream, generation_trace, trace

        agent_response, source_references, images, get_only_images, is_stream, generation_trace = (
            tool_action_execution(
                processed_output,
                BU_Name,
                uploaded_collection_name=uploaded_collection_name,
                trace_id=trace_id,
                regenerate=regenerate,
            )
        )
        return agent_response, source_references, images, get_only_images, is_stream, generation_trace, trace
    except Exception as e:
        log_and_raise_error(
            f"AgentWorkflow -> getKnowledgeResponse: An error occurred: {e}", session_id
        )
