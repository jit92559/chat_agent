# graph/nodes/load_longterm_memory.py

from services.memory_service import get_longterm_memory


async def load_longterm_memory_node(state):
    memory = await get_longterm_memory(state["user_id"])

    return {
        "longterm_memory": memory
    }
