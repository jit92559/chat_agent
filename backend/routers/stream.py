from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime, timezone
import json
import asyncio

from chat_graph.chat_graph import build_chat_graph
from configs.db_config import (
    get_checkpointer,
    messages_collection,
    threads_collection,
)

router = APIRouter(prefix="/api/chat", tags=["Chat"])

checkpointer = get_checkpointer()
graph = build_chat_graph(checkpointer)


class ChatRequest(BaseModel):
    thread_id: str
    message: str
    selected_file_id: str | None = None


@router.post("/stream")
async def stream_chat(req: ChatRequest, request: Request):
    user = request.state.user
    user_id = str(user.get("id") or user.get("_id") or user.get("user_id"))
    email = user.get("email")

    checkpoint_thread_id = f"{user_id}:{req.thread_id}"
    now = datetime.now(timezone.utc)

    await messages_collection.insert_one(
        {
            "user_id": user_id,
            "email": email,
            "thread_id": req.thread_id,
            "role": "user",
            "content": req.message,
            "selected_file_id": req.selected_file_id,
            "created_at": now,
        }
    )

    await threads_collection.update_one(
        {
            "user_id": user_id,
            "thread_id": req.thread_id,
        },
        {
            "$set": {
                "updated_at": now,
            }
        },
    )

    async def save_assistant_message(final_answer: str):
        if not final_answer.strip():
            return

        save_time = datetime.now(timezone.utc)

        await messages_collection.insert_one(
            {
                "user_id": user_id,
                "email": email,
                "thread_id": req.thread_id,
                "role": "assistant",
                "content": final_answer,
                "created_at": save_time,
            }
        )

        await threads_collection.update_one(
            {
                "user_id": user_id,
                "thread_id": req.thread_id,
            },
            {
                "$set": {
                    "updated_at": save_time,
                }
            },
        )

    async def save_error_message(error_msg: str):
        await messages_collection.insert_one(
            {
                "user_id": user_id,
                "email": email,
                "thread_id": req.thread_id,
                "role": "assistant",
                "content": f"Error: {error_msg}",
                "created_at": datetime.now(timezone.utc),
            }
        )

    async def event_generator():
        answer_parts = []

        initial_state = {
            "user_id": user_id,
            "thread_id": req.thread_id,
            "input_text": req.message,
            "selected_file_id": req.selected_file_id,
            "longterm_memory": None,
            "route": None,
            "context": None,
            "web_results": None,
            "answer": None,
        }

        config = {
            "configurable": {
                "thread_id": checkpoint_thread_id
            }
        }

        try:
            async for event in graph.astream_events(
                initial_state,
                config=config,
                version="v2",
            ):
                if await request.is_disconnected():
                    return

                if event["event"] != "on_chat_model_stream":
                    continue

                node_name = event.get("metadata", {}).get("langgraph_node")

                if node_name != "generate_answer":
                    continue

                chunk = event["data"]["chunk"]

                if chunk.content:
                    answer_parts.append(chunk.content)
                    yield f"data: {json.dumps({'token': chunk.content})}\n\n"

            final_answer = "".join(answer_parts)

            yield f"data: {json.dumps({'done': True})}\n\n"

            asyncio.create_task(
                save_assistant_message(final_answer)
            )

        except Exception as e:
            error_msg = str(e)

            if not await request.is_disconnected():
                yield f"data: {json.dumps({'error': error_msg})}\n\n"

            asyncio.create_task(
                save_error_message(error_msg)
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )