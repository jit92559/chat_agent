from services.vectorstore_cache import (
    vectorstore_exists,
    similarity_search_cached,
)


async def rag_context_node(state):
    print(" i am at rag_context_node")
    try:
        user_id = state["user_id"]
        thread_id = state["thread_id"]
        query = state["input_text"]
        selected_file_id = state.get("selected_file_id")

        print("========== RAG DEBUG ==========")
        print("USER:", user_id)
        print("THREAD:", thread_id)
        print("QUERY:", query)
        print("SELECTED_FILE_ID:", selected_file_id)

        if not vectorstore_exists(user_id, thread_id):
            print("NO VECTORSTORE FOUND")

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
            k=6,
            selected_file_id=selected_file_id,
        )

        print("DOCS FOUND:", len(docs))

        for i, doc in enumerate(docs[:3]):
            print("DOC", i + 1, "META:", doc.metadata)
            print("DOC", i + 1, "TEXT:", doc.page_content[:300])

        if not docs:
            return {
                "context": "",
                "web_results": "",
                "retrieved_docs": [],
                "status": "no_context_found",
                "error": None,
            }

        context = "\n\n".join(
            [
                f"""
File: {doc.metadata.get("file_name")}
Type: {doc.metadata.get("file_type")}
File ID: {doc.metadata.get("file_id")}

Content:
{doc.page_content}
"""
                for doc in docs
            ]
        )
        print("RAG CONTEXT LENGTH:", len(context))
        return {
            "context": context,
            "retrieved_docs": [doc.page_content for doc in docs],
            "status": "rag_context_found",
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