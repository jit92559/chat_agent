from langchain_core.messages import SystemMessage, HumanMessage

from llms.chat_llm import get_llm
from schemas.suggestion_response import SuggestionResponse


async def generate_suggestions_node(state):
    print("i am at generate_suggestions_node")

    answer = state.get("answer", "")
    question = state.get("input_text", "")

    if not answer:
        return {"suggestions": []}

    llm = get_llm()

    structured_llm = llm.with_structured_output(
        SuggestionResponse
    )

    response = await structured_llm.ainvoke([
        SystemMessage(
            content="""
Generate follow-up questions.

Rules:

- Generate 0 to 3 questions that can be asked by user.this question should be like asekd by user not you.
- Questions must be relevant.
- Questions must help continue the conversation.
- Keep questions short.
- Do not repeat the user's question.
- Return an empty list if no useful follow-up exists.
"""
        ),
        HumanMessage(
            content=f"""
User Question:
{question}

Assistant Answer:
{answer}
"""
        )
    ])

    print("SUGGESTIONS:", response.suggestions)

    return {
        "suggestions": response.suggestions
    }