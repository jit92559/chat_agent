from dotenv import load_dotenv
load_dotenv()
# llms/chat_model.py

from langchain_ollama import ChatOllama
import os

def get_llm():
    return ChatOllama(
        model=os.getenv("CHAT_MODEL"),
        temperature=0,
    )    