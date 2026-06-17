from langchain_core.messages import HumanMessage
from llms.chat_llm import get_llm


async def router_node(state):
    llm = get_llm()

    prompt = f"""
You are a routing classifier.

Your task is to classify the user's query into EXACTLY ONE route.

AVAILABLE ROUTES

1. normal_chat
Use when:
- General conversation
- Coding questions
- Explanations
- Mathematics
- Reasoning
- Grammar correction
- Writing assistance
- Opinions
- Summarization of user provided text
- Any question answerable without internet or document search

Examples:
"What is Python?"
"Explain FastAPI"
"Correct my English"
"Write a linked list in C++"

--------------------------------------------------

2. internet_search
Use when:
- User asks for latest information
- User asks about current events
- User asks about news
- User asks about today's weather
- User asks about current stock prices
- User asks about recent sports results
- User asks about current government policies
- User asks about anything that may have changed after your training data
- User asks about date,year,month,any events such as dewali , rath yatra

Examples:
"Who won yesterday's IPL match?"
"Weather in Kolkata today"
"Latest AI news"
"Current price of Bitcoin"

--------------------------------------------------

3. rag_context
Use when:
- User asks about uploaded documents
- User asks questions about uploaded PDFs
- User asks questions about uploaded PPTs
- User asks questions about uploaded images
- User refers to:
  - this document
  - this file
  - this PDF
  - this image
  - uploaded file
  - selected file
- User wants information from vector database knowledge

Examples:
"Summarize this PDF"
"What does this document say?"
"Explain chapter 2 of the uploaded file"
"Find the deadline mentioned in the document"

--------------------------------------------------

IMPORTANT RULES

- Return ONLY one route.
- Do NOT explain.
- Do NOT justify.
- Do NOT output JSON.
- Do NOT output code.
- Output exactly one of:

normal_chat
internet_search
rag_context

User Query:
{state["input_text"]}
"""

    result = await llm.ainvoke([HumanMessage(content=prompt)])

    route = result.content.strip().lower()

    if "internet_search" in route:
        route = "internet_search"
    elif "rag_context" in route:
        route = "rag_context"
    else:
        route = "normal_chat"

    return {
        "route": route
    }