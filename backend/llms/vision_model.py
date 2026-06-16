from langchain_ollama import ChatOllama

vision_model = ChatOllama(
    model="llama3.2-vision",
    temperature=0
)