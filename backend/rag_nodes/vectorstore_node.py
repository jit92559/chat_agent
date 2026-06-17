from graph.state import MainState
from pathlib import Path


from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from llms.embedding_model import get_embedding_model

embeddings =get_embedding_model()


def vectorstore_node(state: MainState) -> dict:
    try:
        text = state["extracted_text"]

        if not text or not text.strip():
            return {
                "status": "failed",
                "error": "No extracted text found",
            }

        user_id = state["user_id"]
        thread_id = state["thread_id"]
        file_id = state.get("selected_file_id")

        vectorstore_path = f"storage/vectorstores/{user_id}/{thread_id}"

        Path(vectorstore_path).mkdir(
            parents=True,
            exist_ok=True,
        )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )

        chunks = splitter.split_text(text)

        metadatas = [
            {
                "user_id": user_id,
                "thread_id": thread_id,
                "file_id": file_id,
                "file_name": state.get("file_name"),
                "file_type": state.get("file_type"),
            }
            for _ in chunks
        ]

        if Path(f"{vectorstore_path}/index.faiss").exists():
            vectorstore = FAISS.load_local(
                vectorstore_path,
                embeddings,
                allow_dangerous_deserialization=True,
            )

            vectorstore.add_texts(
                texts=chunks,
                metadatas=metadatas,
            )

        else:
            vectorstore = FAISS.from_texts(
                texts=chunks,
                embedding=embeddings,
                metadatas=metadatas,
            )

        vectorstore.save_local(vectorstore_path)

        return {
            "vectorstore_path": vectorstore_path,
            "status": "vectorstore_updated",
            "error": None,
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
        }