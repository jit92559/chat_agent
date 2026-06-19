from fastapi import APIRouter, UploadFile, File, Request, Query, HTTPException
from fastapi.concurrency import run_in_threadpool

import os
from uuid import uuid4
from datetime import datetime, timezone

from graph.upload_rag_subgraph import build_upload_graph
from configs.db_config import file_uploads_collection

router = APIRouter(prefix="/files", tags=["Files"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

graph = build_upload_graph()


@router.post("/upload-rag")
async def upload_rag_file(
    request: Request,
    thread_id: str = Query(...),
    file: UploadFile = File(...),
):
    try:
        user = request.state.user

        user_id = str(
            user.get("id")
            or user.get("_id")
            or user.get("user_id")
        )
        email = user.get("email") or user.get("sub")

        file_id = str(uuid4())
        file_ext = os.path.splitext(file.filename)[1].lower()
        saved_name = f"{file_id}{file_ext}"

        user_upload_dir = os.path.join(
            UPLOAD_DIR,
            user_id,
            thread_id,
        )

        await run_in_threadpool(
            os.makedirs,
            user_upload_dir,
            exist_ok=True,
        )

        file_path = os.path.join(user_upload_dir, saved_name)

        file_bytes = await file.read()

        def _save_file_sync():
            with open(file_path, "wb") as buffer:
                buffer.write(file_bytes)

        await run_in_threadpool(_save_file_sync)

        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=500,
                detail="File was not saved on server",
            )

        if os.path.getsize(file_path) == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty",
            )

        file_url = f"/uploads/{user_id}/{thread_id}/{saved_name}"

        initial_state = {
            "user_id": user_id,
            "thread_id": thread_id,
            "is_file": True,
            "file_path": file_path,
            "file_name": file.filename,
            "file_type": None,
            "selected_file_id": file_id,
            "vectorstore_path": None,
            "extracted_text": "",
            "route": "",
            "status": "",
            "error": None,
        }

        result = await graph.ainvoke(initial_state)

        if result.get("status") == "failed":
            raise HTTPException(
                status_code=500,
                detail=result.get("error") or "File processing failed",
            )

        vectorstore_path = result.get("vectorstore_path")

        if not vectorstore_path:
            raise HTTPException(
                status_code=500,
                detail="Vectorstore path missing from upload graph result",
            )

        index_path = os.path.join(vectorstore_path, "index.faiss")
        pkl_path = os.path.join(vectorstore_path, "index.pkl")

        if not os.path.exists(index_path) or not os.path.exists(pkl_path):
            raise HTTPException(
                status_code=500,
                detail=f"Vectorstore files not created at {vectorstore_path}",
            )

        now = datetime.now(timezone.utc)

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
            "vectorstore_path": vectorstore_path,
            "status": result.get("status"),
            "error": result.get("error"),
            "created_at": now,
            "updated_at": now,
        }

        await file_uploads_collection.insert_one(file_doc)

        return {
            "success": True,
            "thread_id": thread_id,
            "file": {
                "file_id": file_id,
                "file_name": file.filename,
                "file_type": result.get("file_type"),
                "file_url": file_url,
                "status": result.get("status"),
            },
            "file_id": file_id,
            "file_name": file.filename,
            "file_url": file_url,
            "status": result.get("status"),
            "error": result.get("error"),
            "file_type": result.get("file_type"),
            "vectorstore_path": vectorstore_path,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.get("/thread-files")
async def get_thread_files(
    request: Request,
    thread_id: str = Query(...),
):
    try:
        user = request.state.user

        user_id = str(
            user.get("id")
            or user.get("_id")
            or user.get("user_id")
        )

        cursor = file_uploads_collection.find(
            {
                "user_id": user_id,
                "thread_id": thread_id,
            },
            {
                "_id": 0,
                "file_id": 1,
                "original_file_name": 1,
                "file_type": 1,
                "file_url": 1,
                "status": 1,
                "created_at": 1,
            },
        ).sort("created_at", -1)

        docs = await cursor.to_list(length=None)

        files = [
            {
                "file_id": doc.get("file_id"),
                "file_name": doc.get("original_file_name"),
                "file_type": doc.get("file_type"),
                "file_url": doc.get("file_url"),
                "status": doc.get("status"),
                "created_at": doc.get("created_at"),
            }
            for doc in docs
        ]

        return {
            "success": True,
            "thread_id": thread_id,
            "files": files,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )