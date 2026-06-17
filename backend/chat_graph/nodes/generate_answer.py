from langchain_core.messages import SystemMessage
from llms.chat_llm import get_llm


def generate_answer_node(state):
    llm = get_llm()

    system_prompt = f"""
You are an AI assistant.

INSTRUCTIONS:

1. Answer the user's question directly.
2. Never mention:
   - context
   - web results
   - retrieved documents
   - long-term memory
   - sources
   - reasoning process
3. Never say:
   - "Based on..."
   - "According to..."
   - "From the information provided..."
   - "The context says..."
   - "The web results show..."
4. Do not explain how you got the answer.
5. If information is available, answer naturally as if you already know it.
6. If information is unavailable, say you do not know.
7. Output ONLY the final answer.

Knowledge:
{state.get("context") or ""}

Internet Information:
{state.get("web_results") or ""}

User Profile:
{state.get("longterm_memory") or ""}
"""

    result = llm.invoke([
        SystemMessage(content=system_prompt),
        *state["messages"],
    ])

    return {
        "answer": result.content
    }