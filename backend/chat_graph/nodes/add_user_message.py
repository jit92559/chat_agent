# graph/nodes/add_user_message.py

from langchain_core.messages import HumanMessage


def add_user_message_node(state):
    print("I am add_user_node")
    return {
        "messages": [
            HumanMessage(content=state["input_text"])
        ]
    }