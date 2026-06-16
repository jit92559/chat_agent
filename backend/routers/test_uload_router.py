from fastapi import APIRouter, UploadFile, File
import os
import shutil
from uuid import uuid4

from graph.upload_rag_subgraph import build_upload_graph

router = APIRouter(prefix="/test", tags=["Test Upload RAG"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

graph = build_upload_graph()


@router.post("/upload-rag")
async def test_upload_rag(file: UploadFile = File(...)):
    try:
        file_id = str(uuid4())
        file_ext = os.path.splitext(file.filename)[1]

        saved_name = f"{file_id}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, saved_name)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        initial_state = {
            "messages": [],
            "user_id": "test_user_1",
            "thread_id": "test_thread_1",

            "input_text": None,
            "file_path": file_path,
            "file_name": file.filename,
            "file_type": None,
            "is_file": True,

            "selected_file_id": None,
            "vectorstore_path": None,

            "route": "",
            "answer": "",
            "status": "",
            "error": None,

            "extracted_text": "",
        }

        result = graph.invoke(initial_state)

        return {
            "success": True,
            "file_name": file.filename,
            "status": result.get("status"),
            "error": result.get("error"),
            "file_type": result.get("file_type"),
            "vectorstore_path": result.get("vectorstore_path"),
            "extracted_text_preview": result.get("extracted_text", "")[:3000],
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }