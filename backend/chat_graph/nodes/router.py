# graph/nodes/router.py

from langchain_core.messages import HumanMessage
from llms.chat_llm import get_llm


async def router_node(state):
    print("i am at router_node")
    text = (state.get("input_text") or "").lower()

    rag_keywords = [
        "uploaded",
        "document",
        "pdf",
        "ppt",
        "docx",
        "file",
        "image",
        "this document",
        "this file",
        "this pdf",
        "selected file",
    ]

    if state.get("selected_file_id") or any(k in text for k in rag_keywords):
        return {"route": "rag_context"}

    internet_keywords = [
        "latest",
        "current",
        "today",
        "now",
        "news",
        "weather",
        "stock price",
        "bitcoin price",
        "recent",
        "yesterday",
        "tomorrow",
    ]

    if any(k in text for k in internet_keywords):
        return {"route": "internet_search"}

    llm = get_llm()

    prompt = f"""
You are a routing classifier.

Return exactly one route:

normal_chat
internet_search
rag_context

Rules:

normal_chat:
- General chat
- Coding
- Explanation
- Grammar
- Math
- Writing
- Reasoning

internet_search:
- Latest/current/recent information
- News
- Weather
- Stock/crypto price
- Current policy
- Sports result
- Date-based current event

rag_context:
- Uploaded document/file/PDF/PPT/image
- User asks about selected file
- User asks what this document says

User Query:
{state["input_text"]}

Return only one route.
"""

    result = await llm.ainvoke([HumanMessage(content=prompt)])
    route = result.content.strip().lower()

    if "rag_context" in route:
        route = "rag_context"
    elif "internet_search" in route:
        route = "internet_search"
    else:
        route = "normal_chat"

    return {"route": route}