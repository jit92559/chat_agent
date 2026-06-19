import asyncio

from langchain_core.messages import HumanMessage

from llms.chat_llm import get_llm
from services.memory_service import save_longterm_memory


async def _background_update(
    user_id: str,
    old_memory: str,
    user_message: str,
):
    try:
        llm = get_llm()

        prompt = f"""
You are a memory extraction system.

Existing Memory:
{old_memory}

Latest User Message:
{user_message}

Your task:

Extract ONLY long-term useful information about the user.

Store:
- Name
- Education
- Occupation
- Skills
- Interests
- Goals
- Projects
- Technical preferences
- Learning preferences

Do NOT store:
- Greetings
- Casual chat
- Temporary requests
- Document contents
- Search results
- Assistant responses
- Sensitive information
- One-time questions

If nothing useful should be stored, return:

NO_UPDATE

Otherwise return the FULL updated memory.
Return only memory text.
"""

        result = await llm.ainvoke([
            HumanMessage(content=prompt)
        ])

        updated_memory = result.content.strip()

        if (
            not updated_memory
            or updated_memory == "NO_UPDATE"
            or updated_memory == old_memory
        ):
            return

        await save_longterm_memory(
            user_id=user_id,
            memory=updated_memory,
        )

        print("Memory updated successfully")

    except Exception as e:
        print("Memory update error:", str(e))


async def update_longterm_memory_node(state):
    print("I am at update_longterm_memory_node")

    asyncio.create_task(
        _background_update(
            user_id=state["user_id"],
            old_memory=state.get("longterm_memory") or "",
            user_message=state.get("input_text") or "",
        )
    )

    return {}