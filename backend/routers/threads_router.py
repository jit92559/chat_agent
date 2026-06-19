from fastapi import APIRouter, Request
from uuid import uuid4
from datetime import datetime, timezone

from chat_graph.chat_graph import build_chat_graph
from configs.db_config import threads_collection, get_checkpointer

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