# graph/nodes/final_answer.py

from langchain_core.messages import AIMessage


def final_answer_node(state):
    print("i am at final_answer_node")
    return {
        "messages": [
            AIMessage(content=state["answer"])
        ]
    }