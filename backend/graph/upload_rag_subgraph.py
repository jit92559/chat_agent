from langgraph.graph import StateGraph, START, END

from .state import MainState

from rag_nodes.detect_file_type import (
    detect_file_type_node,
    route_extractor,
)

from rag_nodes.extractor_nodes import (
    pdf_extractor_node,
    ppt_extractor_node,
    doc_extractor_node,
    txt_extractor_node,
    image_extractor_node,
    error_node,
)

from rag_nodes.vectorstore_node import vectorstore_node


def build_upload_graph():
    builder = StateGraph(MainState)

    # Add nodes
    builder.add_node("detect_file_type", detect_file_type_node)

    builder.add_node("pdf_extractor", pdf_extractor_node)
    builder.add_node("ppt_extractor", ppt_extractor_node)
    builder.add_node("doc_extractor", doc_extractor_node)
    builder.add_node("txt_extractor", txt_extractor_node)
    builder.add_node("image_extractor", image_extractor_node)

    builder.add_node("vectorstore", vectorstore_node)
    builder.add_node("error", error_node)

    # Start
    builder.add_edge(START, "detect_file_type")

    # Conditional routing
    builder.add_conditional_edges(
        "detect_file_type",
        route_extractor,
        {
            "pdf": "pdf_extractor",
            "ppt": "ppt_extractor",
            "doc": "doc_extractor",
            "txt": "txt_extractor",
            "image": "image_extractor",
            "error": "error",
        },
    )

    # All extractors go to vectorstore
    builder.add_edge("pdf_extractor", "vectorstore")
    builder.add_edge("ppt_extractor", "vectorstore")
    builder.add_edge("doc_extractor", "vectorstore")
    builder.add_edge("txt_extractor", "vectorstore")
    builder.add_edge("image_extractor", "vectorstore")

    # End
    builder.add_edge("vectorstore", END)
    builder.add_edge("error", END)

    return builder.compile()
