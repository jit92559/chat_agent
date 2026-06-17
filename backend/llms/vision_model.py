from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
load_dotenv()
def get_vision_model():
    vision_model = ChatGoogleGenerativeAI(
        model=os.getenv("VISION_MODEL"),
        temperature=0,
    )
    return vision_model
