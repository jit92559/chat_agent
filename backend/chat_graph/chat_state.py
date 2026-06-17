# graph/state.py

from typing import Optional, Literal
from typing_extensions import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


RouteType = Literal["normal_chat", "internet_search", "rag_context"]


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    user_id: str
    thread_id: str
    input_text: str

    longterm_memory: Optional[str]

    route: Optional[RouteType]

    context: Optional[str]
    web_results: Optional[str]


    selected_file_id: Optional[str]
    vectorstore_path: Optional[str]
    retrieved_docs: list[str]

    
    answer: Optional[str]