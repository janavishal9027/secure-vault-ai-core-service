from pydantic import BaseModel, Field

from app.schemas.search import SearchHit


class RagAnswerRequest(BaseModel):
    owner_user_id: str = Field(..., alias="ownerUserId")
    question: str = Field(..., min_length=1)
    top_k: int | None = Field(default=None, alias="topK", ge=1, le=50)

    model_config = {"populate_by_name": True}


class RagAnswerResponse(BaseModel):
    question: str
    answer: str
    citations: list[SearchHit]
    model: str
