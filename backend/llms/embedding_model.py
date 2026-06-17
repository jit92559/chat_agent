from dotenv import load_dotenv
import os
from langchain_ollama import OllamaEmbeddings


load_dotenv()

def get_embedding_model():
    embeddings = OllamaEmbeddings(
    model=os.getenv("EMBEDDING_MODEL")
    )
    return embeddings