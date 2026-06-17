# services/memory_service.py

from datetime import datetime
from configs.db_config import memory_collection


async def get_longterm_memory(user_id: str) -> str:
    doc = await memory_collection.find_one(
        {"user_id": user_id},
        {"_id": 0, "memory": 1},
    )

    return doc["memory"] if doc else ""

async def save_longterm_memory(user_id: str, memory: str):
    await memory_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "memory": memory,
                "updated_at": datetime.utcnow(),
            }
        },
        upsert=True,
    )