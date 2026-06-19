import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


def get_llm():
    """
    Returns a Google Gemini chat model via langchain-google-genai v4.x.

    langchain-google-genai v4+ uses the new google-genai SDK.
    Correct model names for this version:
      - gemini-2.0-flash        (fast, recommended)
      - gemini-2.0-flash-lite   (fastest, lightest)
      - gemini-2.5-flash        (smarter, slightly slower)
      - gemini-2.5-pro          (most capable)

    The 'gemini-1.5-flash' name only works with the old v1beta API
    and is NOT valid in langchain-google-genai v4+.
    """
    return ChatGoogleGenerativeAI(
        model=os.getenv("CHAT_MODEL", "gemini-2.0-flash"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
    )