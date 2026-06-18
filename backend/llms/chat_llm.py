import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


def get_llm():
    """
    Returns a Google Gemini chat model.

    Why Gemini instead of local Ollama?
    - Ollama runs on your CPU → very slow (30-120s per response)
    - Gemini runs on Google's servers → fast (2-5s per response)
    - Gemini has much better instruction following and RAG accuracy
    - GOOGLE_API_KEY is already set in .env

    Model is configurable via CHAT_MODEL env var.
    Defaults to 'gemini-1.5-flash' (fast, cheap, accurate).
    Use 'gemini-1.5-pro' for higher accuracy on complex tasks.
    """
    return ChatGoogleGenerativeAI(
        model=os.getenv("CHAT_MODEL", "gemini-1.5-flash"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
    )