from fastapi import APIRouter, Request
from uuid import uuid4
from datetime import datetime, timezone

from configs.db_config import threads_collection

router = APIRouter(prefix="/threads", tags=["Threads"])


@router.post("/new")
async def create_new_chat(request: Request):
    user = request.state.user

    user_id = user["user_id"]
    email = user["sub"]

    thread_id = str(uuid4())

    thread_doc = {
        "thread_id": thread_id,
        "user_id": user_id,
        "email": email,
        "title": thread_id,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    await threads_collection.insert_one(thread_doc)

    return {
        "success": True,
        "thread_id": thread_id,
        "title": thread_id,
    }
@router.get("/")
async def get_user_threads(request: Request):
    user = request.state.user
    user_id = user["user_id"]

    cursor = threads_collection.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("updated_at", -1)

    threads = await cursor.to_list(length=None)

    return {
        "success": True,
        "threads": threads,
    }