from langchain_core.messages import HumanMessage
from llms.chat_llm import get_llm
from services.memory_service import save_longterm_memory


async def update_longterm_memory_node(state):
    print("i am at update_longterm mermory_node")
    llm = get_llm()

    old_memory = state.get("longterm_memory") or ""
    user_message = state.get("input_text") or ""
    assistant_answer = state.get("answer") or ""

    prompt = f"""
Update the user's long-term memory.

Existing memory:
{old_memory}

New user message:
{user_message}

Assistant answer:
{assistant_answer}

Rules:
- Store only stable useful facts.
- Store project preferences, long-term goals, technical choices.
- Do not store temporary random chat.
- Return the full updated memory.
- If nothing useful, return existing memory unchanged.

Return only memory text.
"""

    result = await llm.ainvoke(
        [HumanMessage(content=prompt)]
    )

    updated_memory = result.content.strip()

    await save_longterm_memory(
        user_id=state["user_id"],
        memory=updated_memory,
    )

    return {
        "longterm_memory": updated_memory
    }