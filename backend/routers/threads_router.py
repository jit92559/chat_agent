# routers/thread_router.py

import os
import shutil
import asyncio

from fastapi import APIRouter, Request, HTTPException

from configs.db_config import (
    threads_collection,
    file_uploads_collection,
    sync_client,
    CHECK_DB,
    get_checkpointer
)


from uuid import uuid4
from datetime import datetime, timezone

from chat_graph.chat_graph import build_chat_graph


router = APIRouter(prefix="/threads", tags=["Threads"])

checkpointer = get_checkpointer()
graph = build_chat_graph(checkpointer)


@router.post("/new")
async def create_new_chat(request: Request):
    user = request.state.user

    user_id = str(
        user.get("id")
        or user.get("_id")
        or user.get("user_id")
    )

    email = user.get("email") or user.get("sub")

    thread_id = str(uuid4())
    now = datetime.now(timezone.utc)

    thread_doc = {
        "thread_id": thread_id,
        "user_id": user_id,
        "email": email,
        "title": "New Chat",
        "created_at": now,
        "updated_at": now,
    }

    await threads_collection.insert_one(thread_doc)

    return {
        "success": True,
        "thread_id": thread_id,
        "title": "New Chat",
    }


@router.get("/")
async def get_user_threads(request: Request):
    user = request.state.user

    user_id = str(
        user.get("id")
        or user.get("_id")
        or user.get("user_id")
    )

    cursor = threads_collection.find(
        {"user_id": user_id},
        {"_id": 0},
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

        checkpoint_thread_id = f"{user_id}:{thread_id}"

        config = {
            "configurable": {
                "thread_id": checkpoint_thread_id
            }
        }

        checkpoint_state = await graph.aget_state(config)

        values = checkpoint_state.values or {}

        raw_messages = values.get("messages", [])
        suggestions = values.get("suggestions", [])

        messages = []

        # Find the last assistant message
        last_assistant_index = None

        for i, msg in enumerate(raw_messages):
            if getattr(msg, "type", "") == "ai":
                last_assistant_index = i

        # Build response messages
        for i, msg in enumerate(raw_messages):
            role = getattr(msg, "type", "")
            content = getattr(msg, "content", "")

            if role == "human":
                role = "user"
            elif role == "ai":
                role = "assistant"

            message = {
                "role": role,
                "content": content,
            }

            # Attach suggestions ONLY to the latest assistant message
            if (
                role == "assistant"
                and i == last_assistant_index
                and suggestions
            ):
                message["suggestions"] = suggestions

            messages.append(message)

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
    



@router.delete("/{thread_id}")
async def delete_thread(thread_id: str, request: Request):
    try:
        user = request.state.user

        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        user_id = str(
            user.get("id")
            or user.get("_id")
            or user.get("user_id")
        )

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user")

        full_thread_id = f"{user_id}:{thread_id}"

        # ----------------------------
        # Check thread exists
        # ----------------------------
        thread = await threads_collection.find_one(
            {"user_id": user_id, "thread_id": thread_id}
        )

        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")

        # =========================================================
        # 1. DELETE FILE METADATA (Mongo)
        # =========================================================
        await file_uploads_collection.delete_many(
            {"user_id": user_id, "thread_id": thread_id}
        )

        # =========================================================
        # 2. DELETE UPLOADED FILES (uploads folder)
        # =========================================================
        upload_dir = os.path.abspath(
            os.path.join("uploads", user_id, thread_id)
        )

        base_upload = os.path.abspath("uploads")

        if upload_dir.startswith(base_upload) and os.path.exists(upload_dir):
            shutil.rmtree(upload_dir)

        # =========================================================
        # 3. DELETE VECTOR STORE (storage folder)  ⭐ NEW
        # =========================================================
        vector_dir = os.path.abspath(
            os.path.join("storage","vectorstores" ,user_id, thread_id)
        )

        base_storage = os.path.abspath("storage")

        if vector_dir.startswith(base_storage) and os.path.exists(vector_dir):
            shutil.rmtree(vector_dir)

        # =========================================================
        # 4. DELETE LANGGRAPH CHECKPOINTS
        # =========================================================
        checkpoint_db = sync_client[CHECK_DB]

        await asyncio.to_thread(
            checkpoint_db["checkpoints"].delete_many,
            {"thread_id": full_thread_id},
        )

        await asyncio.to_thread(
            checkpoint_db["checkpoint_writes"].delete_many,
            {"thread_id": full_thread_id},
        )

        # =========================================================
        # 5. DELETE THREAD DOCUMENT
        # =========================================================
        result = await threads_collection.delete_one(
            {"user_id": user_id, "thread_id": thread_id}
        )

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Thread already deleted or not found",
            )

        return {
            "success": True,
            "message": "Thread, files, vector store & checkpoints deleted successfully",
            "thread_id": thread_id,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )