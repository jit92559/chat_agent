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


def route_after_extraction(state: MainState) -> str:
    if state.get("status") == "failed":
        return "error"

    extracted_text = state.get("extracted_text")

    if not extracted_text or not extracted_text.strip():
        return "error"

    return "vectorstore"


def build_upload_graph():
    builder = StateGraph(MainState)

    builder.add_node("detect_file_type", detect_file_type_node)

    builder.add_node("pdf_extractor", pdf_extractor_node)
    builder.add_node("ppt_extractor", ppt_extractor_node)
    builder.add_node("doc_extractor", doc_extractor_node)
    builder.add_node("txt_extractor", txt_extractor_node)
    builder.add_node("image_extractor", image_extractor_node)

    builder.add_node("vectorstore", vectorstore_node)
    builder.add_node("error", error_node)

    builder.add_edge(START, "detect_file_type")

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

    for extractor in [
        "pdf_extractor",
        "ppt_extractor",
        "doc_extractor",
        "txt_extractor",
        "image_extractor",
    ]:
        builder.add_conditional_edges(
            extractor,
            route_after_extraction,
            {
                "vectorstore": "vectorstore",
                "error": "error",
            },
        )

    builder.add_edge("vectorstore", END)
    builder.add_edge("error", END)

    return builder.compile()