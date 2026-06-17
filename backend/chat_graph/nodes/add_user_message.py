# graph/nodes/add_user_message.py

from langchain_core.messages import HumanMessage


def add_user_message_node(state):
    return {
        "messages": [
            HumanMessage(content=state["input_text"])
        ]
    }