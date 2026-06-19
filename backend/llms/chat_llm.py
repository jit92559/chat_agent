import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama

load_dotenv(override=True)


def get_llm():
    """
    Fast Ollama setup:
    - model: llama3.2:1b  → 3x faster than llama3.2 (3B), still very capable
    - num_predict: 512    → cap max output tokens (prevents runaway long responses)
    - num_ctx: 2048       → smaller context window = faster per-token generation
    - temperature: 0      → deterministic, no sampling overhead
    """
    return ChatOllama(
        model=os.getenv("CHAT_MODEL", "llama3.2:1b"),
        temperature=0,
        num_predict=int(os.getenv("LLM_MAX_TOKENS", "512")),
        num_ctx=int(os.getenv("LLM_CTX_SIZE", "2048")),
    )