from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from chat_graph.chat_graph import build_chat_graph
from configs.db_config import get_checkpointer
router = APIRouter(prefix="/api/chat", tags=["Chat"])
checkpointer=get_checkpointer()
graph = build_chat_graph(checkpointer)


class ChatRequest(BaseModel):
    thread_id: str
    message: str
    selected_file_id:str|None=None

@router.post("/stream")
async def stream_chat(req: ChatRequest, request: Request):
    # user = request.state.user
    # user_id = str(user.get("id") or user.get("_id"))
    user_id='id1'
    checkpoint_thread_id = f"{user_id}:{req.thread_id}"

    async def event_generator():
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

        async for event in graph.astream_events(
            initial_state,
            config=config,
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":

                node_name = event.get("metadata", {}).get("langgraph_node")

                if node_name != "generate_answer":
                    continue

                chunk = event["data"]["chunk"]

                if chunk.content:
                    yield f"data: {json.dumps({'token': chunk.content})}\n\n"

        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )