from fastapi import APIRouter, UploadFile, File, Request, Query
import os
import shutil
from uuid import uuid4
from datetime import datetime, timezone

from graph.upload_rag_subgraph import build_upload_graph
from configs.db_config import file_uploads_collection

router = APIRouter(prefix="/files", tags=["Test Upload RAG"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

graph = build_upload_graph()


@router.post("/upload-rag")
async def test_upload_rag(
    request: Request,
    thread_id: str = Query(...),
    file: UploadFile = File(...),
):
    try:
        # user = request.state.user

        user_id = "user_id1"
        email = 'monojitbairagi0@gmail.com'

        file_id = str(uuid4())
        file_ext = os.path.splitext(file.filename)[1]

        saved_name = f"{file_id}{file_ext}"

        user_upload_dir = os.path.join(
            UPLOAD_DIR,
            user_id,
            thread_id,
        )
        os.makedirs(user_upload_dir, exist_ok=True)

        file_path = os.path.join(user_upload_dir, saved_name)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_url = f"/uploads/{user_id}/{thread_id}/{saved_name}"

        initial_state = {
            "messages": [],

            "user_id": user_id,
            "thread_id": thread_id,

            "input_text": None,

            "file_path": file_path,
            "file_name": file.filename,
            "file_type": None,
            "is_file": True,

            "selected_file_id": file_id,
            "vectorstore_path": None,

            "extracted_text": "",
            "retrieved_docs": [],
            "context": None,

            "route": "",
            "answer": "",
            "status": "",
            "error": None,
        }

        result = graph.invoke(initial_state)

        file_doc = {
            "file_id": file_id,
            "user_id": user_id,
            "email": email,
            "thread_id": thread_id,

            "original_file_name": file.filename,
            "saved_file_name": saved_name,

            "file_path": file_path,
            "file_url": file_url,

            "file_type": result.get("file_type"),
            "vectorstore_path": result.get("vectorstore_path"),

            "status": result.get("status"),
            "error": result.get("error"),

            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        await file_uploads_collection.insert_one(file_doc)

        return {
            "success": result.get("status") != "failed",
            "user_id": user_id,
            "email": email,
            "thread_id": thread_id,
            "file_id": file_id,
            "file_name": file.filename,
            "file_url": file_url,
            "status": result.get("status"),
            "error": result.get("error"),
            "file_type": result.get("file_type"),
            "vectorstore_path": result.get("vectorstore_path"),
            "extracted_text_preview": result.get("extracted_text", "")[:1000],
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }