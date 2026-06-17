from services.vectorstore_cache import (
    vectorstore_exists,
    similarity_search_cached,
)


async def rag_context_node(state):
    try:
        user_id = state["user_id"]
        thread_id = state["thread_id"]
        query = state["input_text"]
        selected_file_id = state.get("selected_file_id")

        if not vectorstore_exists(user_id, thread_id):
            return {
                "context": "",
                "web_results": "",
                "retrieved_docs": [],
                "status": "no_vectorstore_found",
                "error": None,
            }

        docs = await similarity_search_cached(
            user_id=user_id,
            thread_id=thread_id,
            query=query,
            k=4,
            selected_file_id=selected_file_id,
        )

        context = "\n\n".join(
            [
                f"""
File: {doc.metadata.get("file_name")}
Type: {doc.metadata.get("file_type")}
Content:
{doc.page_content}
"""
                for doc in docs
            ]
        )

        return {
            "context": context,
            "web_results": "",
            "retrieved_docs": [doc.page_content for doc in docs],
            "status": "rag_context_found" if docs else "no_context_found",
            "error": None,
        }

    except Exception as e:
        return {
            "context": "",
            "web_results": "",
            "retrieved_docs": [],
            "status": "rag_failed",
            "error": str(e),
        }