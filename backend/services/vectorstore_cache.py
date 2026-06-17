from pathlib import Path
from functools import partial
from threading import Lock

from fastapi.concurrency import run_in_threadpool
from langchain_community.vectorstores import FAISS

from llms.embedding_model import get_embedding_model


embeddings = get_embedding_model()

_VECTORSTORE_CACHE = {}
_CACHE_LOCK = Lock()


def _cache_key(user_id: str, thread_id: str) -> str:
    return f"{user_id}:{thread_id}"


def _vectorstore_path(user_id: str, thread_id: str) -> str:
    return f"storage/vectorstores/{user_id}/{thread_id}"


def vectorstore_exists(user_id: str, thread_id: str) -> bool:
    path = _vectorstore_path(user_id, thread_id)
    return Path(f"{path}/index.faiss").exists()


async def get_vectorstore(user_id: str, thread_id: str):
    key = _cache_key(user_id, thread_id)
    path = _vectorstore_path(user_id, thread_id)

    with _CACHE_LOCK:
        cached = _VECTORSTORE_CACHE.get(key)

    if cached is not None:
        return cached

    vectorstore = await run_in_threadpool(
        FAISS.load_local,
        path,
        embeddings,
        allow_dangerous_deserialization=True,
    )

    with _CACHE_LOCK:
        _VECTORSTORE_CACHE[key] = vectorstore

    return vectorstore


def invalidate_vectorstore(user_id: str, thread_id: str):
    key = _cache_key(user_id, thread_id)

    with _CACHE_LOCK:
        _VECTORSTORE_CACHE.pop(key, None)


def clear_vectorstore_cache():
    with _CACHE_LOCK:
        _VECTORSTORE_CACHE.clear()


async def similarity_search_cached(
    user_id: str,
    thread_id: str,
    query: str,
    k: int = 4,
    selected_file_id: str | None = None,
):
    vectorstore = await get_vectorstore(user_id, thread_id)

    if selected_file_id:
        return await run_in_threadpool(
            partial(
                vectorstore.similarity_search,
                query,
                k=k,
                filter={"file_id": selected_file_id},
            )
        )

    return await run_in_threadpool(
        partial(
            vectorstore.similarity_search,
            query,
            k=k,
        )
    )