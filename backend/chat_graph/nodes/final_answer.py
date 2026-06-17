# graph/nodes/final_answer.py

from langchain_core.messages import AIMessage


def final_answer_node(state):
    return {
        "messages": [
            AIMessage(content=state["answer"])
        ]
    }