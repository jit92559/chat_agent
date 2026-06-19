
import asyncio
from langchain_core.messages import HumanMessage
from llms.chat_llm import get_llm
from services.memory_service import save_longterm_memory


async def _background_update(user_id: str, old_memory: str, user_message: str, assistant_answer: str):
    """
    Runs in the background after the response is already streamed.
    User never waits for this.
    """
    try:
        llm = get_llm()

        prompt = f"""Update the user's long-term memory.

Existing memory:
{old_memory}

New user message:
{user_message}

Assistant answer:
{assistant_answer}

Rules:
- Store only stable useful facts (name, skills, preferences, goals).
- Skip casual or one-off messages.
- Return the full updated memory or the existing memory if nothing changed.

Return only the memory text, nothing else."""

        result = await llm.ainvoke([HumanMessage(content=prompt)])
        updated_memory = result.content.strip()
        await save_longterm_memory(user_id=user_id, memory=updated_memory)
    except Exception:
        # Memory update failure should never affect the chat response
        pass


async def update_longterm_memory_node(state):
    """
    Fires memory update in the background — does NOT block the response stream.
    The user sees their answer immediately; memory is updated asynchronously.
    """
    asyncio.create_task(
        _background_update(
            user_id=state["user_id"],
            old_memory=state.get("longterm_memory") or "",
            user_message=state.get("input_text") or "",
            assistant_answer=state.get("answer") or "",
        )
    )

    # Return immediately — don't await the memory update
    return {}