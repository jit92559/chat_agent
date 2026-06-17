from fastapi import APIRouter, Request
from uuid import uuid4
from datetime import datetime, timezone

from configs.db_config import (threads_collection,messages_collection)

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

@router.get("/{thread_id}/messages")
async def get_thread_messages(
    request: Request,
    thread_id: str,
):
    try:
        user = request.state.user

        user_id = str(
            user.get("id")
            or user.get("_id")
            or user.get("user_id")
        )

        cursor = messages_collection.find(
            {
                "user_id": user_id,
                "thread_id": thread_id,
            },
            {
                "_id": 0,
            },
        ).sort("created_at", 1)

        messages = await cursor.to_list(length=None)

        return {
            "success": True,
            "thread_id": thread_id,
            "messages": messages,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "messages": [],
        }