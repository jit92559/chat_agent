"""
router.py - Keyword-based router (zero LLM calls)

WHY: The original router called the LLM just to classify the route — that was
an entire inference pass (20-40s on CPU) wasted before the actual answer even started.

This version uses fast keyword/pattern matching instead.
Same accuracy for clear-cut queries, instant execution (< 1ms).
"""

# Keywords that strongly indicate web/internet search is needed
INTERNET_KEYWORDS = {
    "today", "current", "latest", "now", "live", "real-time",
    "news", "weather", "price", "stock", "score", "result",
    "who won", "happening", "recent", "this week", "this month",
    "right now", "at the moment", "currently", "update",
}

# Keywords that indicate the user is referring to an uploaded document
RAG_KEYWORDS = {
    "document", "file", "pdf", "ppt", "pptx", "docx", "doc",
    "uploaded", "this file", "this doc", "this pdf", "the file",
    "resume", "report", "summarize this", "explain this",
    "what does it say", "in the document", "from the file",
    "according to the file", "mention", "chapter", "page",
}


async def router_node(state):
    """
    Classifies the user query into one of:
      - normal_chat     (default)
      - internet_search (time-sensitive / current events)
      - rag_context     (user asks about an uploaded file)

    Uses keyword matching — no LLM call needed.
    """
    query = (state.get("input_text") or "").lower()
    selected_file_id = state.get("selected_file_id")

    # If a file is explicitly selected in the UI, always use RAG
    if selected_file_id:
        return {"route": "rag_context"}

    # Check for RAG keywords first (more specific)
    if any(kw in query for kw in RAG_KEYWORDS):
        return {"route": "rag_context"}

    # Check for internet search keywords
    if any(kw in query for kw in INTERNET_KEYWORDS):
        return {"route": "internet_search"}

    # Default: normal conversation
    return {"route": "normal_chat"}