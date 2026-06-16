from typing import Optional, Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class MainState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    user_id: str
    thread_id: str

    input_text: Optional[str]

    is_file: bool
    file_path: Optional[str]
    file_name: Optional[str]
    file_type: Optional[str]

    selected_file_id: Optional[str]
    vectorstore_path: Optional[str]

    extracted_text: Optional[str]

    retrieved_docs: list[str]
    context: Optional[str]

    route: str

    answer: str

    status: str
    error: Optional[str]