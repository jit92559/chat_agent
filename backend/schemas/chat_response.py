from pydantic import BaseModel, Field


class ChatResponse(BaseModel):
    answer: str = Field(description="Answer to the user's question")

    suggestions: list[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions"
    )