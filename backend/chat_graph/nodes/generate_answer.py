from langchain_core.messages import SystemMessage, HumanMessage

from llms.chat_llm import get_llm


async def generate_answer_node(state):
    print("i am at generate_ans_node")

    llm = get_llm()

    route = state.get("route")
    context = (state.get("context") or "").strip()
    web_results = (state.get("web_results") or "").strip()
    memory = (state.get("longterm_memory") or "").strip()
    question = state.get("input_text") or ""
    messages = state.get("messages", [])

    print("========== GENERATE DEBUG ==========")
    print("ROUTE:", route)
    print("STATUS:", state.get("status"))
    print("CONTEXT LENGTH:", len(context))
    print("WEB LENGTH:", len(web_results))
    print("SELECTED FILE:", state.get("selected_file_id"))

    if route == "internet_search":

        system_prompt = f"""
You are a helpful AI assistant.

The Internet Information section contains real search results.

Instructions:

- Use Internet Information as the primary source.
- Answer the user's question directly.
- Never say:
  - I don't have internet access
  - I cannot browse the internet
  - I don't have real-time information
  - I cannot access current news
- Do not mention search results, retrieval systems, tools, context, or sources.
- If Internet Information is available, use it.
- If Internet Information is insufficient, use general knowledge when appropriate.
- Do not invent recent facts.
-ask question to user to maintain conversation flow

Internet Information:
{web_results}

"""

    elif route == "rag_context":

        system_prompt = f"""
You are a helpful AI assistant.

The Document Knowledge section contains content from uploaded documents.

Instructions:

- Use Document Knowledge as the primary source.
- Answer confidently when the answer exists in the document.
- Never say:
  - I cannot access the document
  - I cannot see the file
  - I don't have access to uploaded files
- Do not mention chunks, embeddings, retrieval, vector databases, context, or sources.
- If Document Knowledge is insufficient, use general knowledge when appropriate.
- Do not invent document content.
-ask question to user to maintain conversation flow

Document Knowledge:
{context}

"""

    else:

        system_prompt = f"""
You are a helpful AI assistant.

Instructions:

- Answer clearly and directly.
- Use reasoning and general knowledge.
- Use user profile information if useful.
-ask question to user to maintain conversation flow

User Profile:
{memory}


"""

    result = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        *messages,
        HumanMessage(content=question)
    ])

    return {
        "answer": result.content
    }