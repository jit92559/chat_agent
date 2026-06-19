from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from chat_graph.chat_graph import build_chat_graph
from configs.db_config import get_checkpointer

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

    user_id = str(
        user.get("id")
        or user.get("_id")
        or user.get("user_id")
    )

    checkpoint_thread_id = f"{user_id}:{req.thread_id}"

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
            "suggestions": [],
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

                # Stream only answer tokens
                if event["event"] != "on_chat_model_stream":
                    continue

                node_name = event.get("metadata", {}).get(
                    "langgraph_node"
                )

                if node_name != "generate_answer":
                    continue

                chunk = event["data"]["chunk"]

                if not chunk.content:
                    continue

                answer_parts.append(chunk.content)

                yield (
                    f"data: {json.dumps({
                        'type': 'token',
                        'token': chunk.content
                    })}\n\n"
                )

            final_answer = "".join(answer_parts)

            # Read final graph state
            suggestions = []

            try:
                final_state = await graph.aget_state(config)

                print("\n========== FINAL STATE ==========")

                if (
                    final_state
                    and hasattr(final_state, "values")
                    and isinstance(final_state.values, dict)
                ):
                    print(final_state.values)

                    suggestions = final_state.values.get(
                        "suggestions",
                        []
                    )

            except Exception as state_error:
                print(
                    "STATE FETCH ERROR:",
                    str(state_error)
                )

            # Final SSE event
            yield (
                f"data: {json.dumps({
                    'type': 'complete',
                    'done': True,
                    'answer': final_answer,
                    'suggestions': suggestions
                })}\n\n"
            )

        except Exception as e:
            print("STREAM ERROR:", str(e))

            if not await request.is_disconnected():
                yield (
                    f"data: {json.dumps({
                        'type': 'error',
                        'error': str(e)
                    })}\n\n"
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