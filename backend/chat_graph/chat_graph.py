# graph/chat_graph.py

from langgraph.graph import StateGraph, START, END

from .chat_state import ChatState

from .nodes.load_longterm_memory import load_longterm_memory_node
from .nodes.add_user_message import add_user_message_node
from .nodes.internet_search import internet_search_node
from .nodes.router import router_node
from .nodes.rag_context import rag_context_node
from .nodes.generate_answer import generate_answer_node
from .nodes.update_longterm_memory import update_longterm_memory_node
from .nodes.generate_suggestions_node import generate_suggestions_node
from .nodes.final_answer import final_answer_node


def route_decision(state: ChatState):
    route = state.get("route") or "normal_chat"

    if route not in ["normal_chat", "internet_search", "rag_context"]:
        return "normal_chat"

    return route


def rag_result_decision(state: ChatState):
    status = state.get("status")

    if status == "rag_context_found":
        return "generate_answer"

    return "generate_answer"


def build_chat_graph(checkpointer=None):
    graph = StateGraph(ChatState)

    graph.add_node("load_longterm_memory", load_longterm_memory_node)
    graph.add_node("add_user_message", add_user_message_node)
    graph.add_node("router", router_node)

    graph.add_node("internet_search", internet_search_node)
    graph.add_node("rag_context", rag_context_node)

    graph.add_node("generate_answer", generate_answer_node)

    graph.add_node(
    "generate_suggestions",
    generate_suggestions_node
)
    graph.add_node("update_longterm_memory", update_longterm_memory_node)
    graph.add_node("final_answer", final_answer_node)


    graph.add_edge(START, "load_longterm_memory")
    graph.add_edge("load_longterm_memory", "add_user_message")
    graph.add_edge("add_user_message", "router")

    graph.add_conditional_edges(
        "router",
        route_decision,
        {
            "normal_chat": "generate_answer",
            "internet_search": "internet_search",
            "rag_context": "rag_context",
        },
    )

    graph.add_edge("internet_search", "generate_answer")

    graph.add_conditional_edges(
        "rag_context",
        rag_result_decision,
        {
            "generate_answer": "generate_answer",
        },
    )

    graph.add_edge("generate_answer", "generate_suggestions")
    graph.add_edge("generate_suggestions", "update_longterm_memory")
    graph.add_edge("update_longterm_memory", "final_answer")
    graph.add_edge("final_answer", END)
    return graph.compile(checkpointer=checkpointer)