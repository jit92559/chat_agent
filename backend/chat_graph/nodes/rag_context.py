# graph/nodes/rag_context.py

from pathlib import Path
from langchain_community.vectorstores import FAISS

from llms.embedding_model import get_embedding_model


embeddings = get_embedding_model()


async def rag_context_node(state):
    try:
        user_id = state["user_id"]
        thread_id = state["thread_id"]
        query = state["input_text"]

        selected_file_id = state.get("selected_file_id")

        vectorstore_path = f"storage/vectorstores/{user_id}/{thread_id}"

        if not Path(f"{vectorstore_path}/index.faiss").exists():
            return {
                "context": "",
                "web_results": "",
                "retrieved_docs": [],
                "status": "no_vectorstore_found",
                "error": None,
            }

        vectorstore = FAISS.load_local(
            vectorstore_path,
            embeddings,
            allow_dangerous_deserialization=True,
        )

        # Case 1: user selected one file
        if selected_file_id:
            docs = vectorstore.similarity_search(
                query,
                k=4,
                filter={
                    "file_id": selected_file_id
                },
            )

        # Case 2: user selected no file
        # search from entire thread vectorstore
        else:
            docs = vectorstore.similarity_search(
                query,
                k=4,
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