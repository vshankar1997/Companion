from typing import List, Optional
from numpy import add
from pydantic import BaseModel, Field
from ai_core.function_calling_utils import convert_pydantic_to_openai_tool
from enum import Enum


class AnswerDepthEnum(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class KnowledgeBaseAssistant(BaseModel):
    """An expert assistant that provides highly tailored responses from the knowledge database in the Medical Affairs domain."""

    user_question: str = Field(
        ...,
        description="The complete user query, including any relevant context from prior interactions. This input is crucial for searching and retrieving precise information from the knowledge database.",
    )
    search_queries: List[str] = Field(
        ...,
        description="A series of detailed and structured search queries derived from the user's question. These queries are formulated to cover all potential aspects and nuances of the user's inquiry.",
    )
    preliminary_answer: str = Field(
        ...,
        description="An initial hypothesis or potential answer based on the initial understanding of the user's question. This serves as a starting point for further refinement and validation of the final response.",
    )
    answer_depth: AnswerDepthEnum = Field(
        ...,
        description="The required level of detail for the answer. Options include 'Low' for a brief overview, 'Medium' for an in-depth explanation, and 'High' for a comprehensive analysis. If not specified, the default is 'Medium'. The depth of the answer should be 'High'  or 'Low' Only when the user explicitly requests it. Otherwise, the default should be 'Medium'.",
    )
    additional_instructions: str = Field(
        ...,
        description="Any additional instructions, any format and style preferences, or specific details provided by the user to ensure an accurate and comprehensive response. This may include specific data points that the users wants to be included in the answer, any format or structure that the user wants the answer in, or any other relevant information. Be clear and descriptive to ensure the response meets your expectations.",
    )
    show_only_images: bool = Field(
        ...,
        description="Default value is False. True if user specifically asked to only retrieve and show/display/print/provide any kind of image or figure and does not require textual response. False If reponse requires both explaination in Text and to show visuals.If answer or reponse mandatorily ONLY requires to show any kind of image (example includes flowcharts, diagrams, graphs, figures etc.) basically any visual representation then return this values as True and does not require any explaination.If not required then keep it False.",
    )

class InternalKnowledgeBase(BaseModel):
    """InternalDocsknowledgeBase: Use this tool Exclusively for answering **Internal** queries. Use only when users explicitly request information from **Internal Documents**. User needs to mention the word **Internal** in the question."""

    user_question: str = Field(
        ...,
        description="The complete user query, including any relevant context from prior interactions. This input is crucial for searching and retrieving precise information from the knowledge database.",
    )
    search_queries: List[str] = Field(
        ...,
        description="A series of detailed and structured search queries derived from the user's question. These queries are formulated to cover all potential aspects and nuances of the user's inquiry.",
    )
    preliminary_answer: str = Field(
        ...,
        description="An initial hypothesis or potential answer based on the initial understanding of the user's question. This serves as a starting point for further refinement and validation of the final response.",
    )
    answer_depth: AnswerDepthEnum = Field(
        ...,
        description="The required level of detail for the answer. Options include 'Low' for a brief overview, 'Medium' for an in-depth explanation, and 'High' for a comprehensive analysis. If not specified, the default is 'Medium'. The depth of the answer should be 'High'  or 'Low' Only when the user explicitly requests it. Otherwise, the default should be 'Medium'.",
    )
    additional_instructions: str = Field(
        ...,
        description="Any additional instructions, any format and style preferences, or specific details provided by the user to ensure an accurate and comprehensive response. This may include specific data points that the users wants to be included in the answer, any format or structure that the user wants the answer in, or any other relevant information. Be clear and descriptive to ensure the response meets your expectations.",
    )


class UploadedKnowledgeBase(BaseModel):
    """Use this tool to answer all general queries."""

    user_question: str = Field(
        ...,
        description="The complete user query, including any relevant context from prior interactions. This input is crucial for searching and retrieving precise information from the knowledge database.",
    )
    search_queries: List[str] = Field(
        ...,
        description="A series of detailed and structured search queries derived from the user's question. These queries are formulated to cover all potential aspects and nuances of the user's inquiry.",
    )
    preliminary_answer: str = Field(
        ...,
        description="An initial hypothesis or potential answer based on the initial understanding of the user's question. This serves as a starting point for further refinement and validation of the final response.",
    )
    answer_depth: AnswerDepthEnum = Field(
        ...,
        description="The required level of detail for the answer. Options include 'Low' for a brief overview, 'Medium' for an in-depth explanation, and 'High' for a comprehensive analysis. If not specified, the default is 'Medium'. The depth of the answer should be 'High'  or 'Low' Only when the user explicitly requests it. Otherwise, the default should be 'Medium'.",
    )
    additional_instructions: str = Field(
        ...,
        description="Any additional instructions, any format and style preferences, or specific details provided by the user to ensure an accurate and comprehensive response. This may include specific data points that the users wants to be included in the answer, any format or structure that the user wants the answer in, or any other relevant information. Be clear and descriptive to ensure the response meets your expectations.",
    )


class SummarizeUploadedDocuments(BaseModel):
    """This tool summarizes uploaded PDFs or documents. Use it to request a full document summary rather than a summary of specific topics within the document.This captures detailed requirements for summarizing uploaded documents. It is designed to understand the user's needs thoroughly and provide a highly tailored summary."""

    document_names: List[str] = Field(
        ...,
        description="List of document names to be summarized. Ensure the exact names are provided to avoid any confusion. Provide all the document names that need to be summarized at once.",
    )
    summary_objective: str = Field(
        ...,
        description="A detailed description of the summary type desired. Specify if it's an executive summary, a detailed analysis, an abstract, etc.",
    )
    key_focus_areas: List[str] = Field(
        ...,
        description="A list of specific sections, themes, or data points to emphasize in the summary. This helps in tailoring the summary to highlight critical aspects.",
    )
    desired_length: str = Field(
        ...,
        description="Indicate the preferred length of the summary (e.g., brief overview, one-page summary, multi-page detailed summary).",
    )
    additional_instructions: str = Field(
        ...,
        description="Any additional context, instructions, or preferences that can aid in crafting the summary as per the users needs.",
    )

class ComparingDocumentsAssistant(BaseModel):
    """This tool compares two uploaded PDFs or documents. Use it to request a detailed comparison between two documents. This captures detailed requirements for comparing uploaded documents. It is designed to understand the user's needs thoroughly and provide a highly tailored comparison."""

    document_name_1: str = Field(
        ...,
        description="The name of the first document to be compared.",
    )
    document_name_2: str = Field(
        ...,
        description="The name of the Second document to be compared.",
    )
    comparison_areas: Optional[List[str]] = Field(
        ...,
        description="A list of focus areas mentioned in user question on which comparison of documents is required. This helps in tailoring the comparison to highlight critical aspects. **Mention key_focus_areas only if user explicitly mentions it.** ",
    )

tool_models = [
    KnowledgeBaseAssistant,
]
upload_tools_models = [
    UploadedKnowledgeBase,
    InternalKnowledgeBase,
    SummarizeUploadedDocuments,
    ComparingDocumentsAssistant
]

tools = [convert_pydantic_to_openai_tool(model) for model in tool_models]
upload_tools = [convert_pydantic_to_openai_tool(model) for model in upload_tools_models]