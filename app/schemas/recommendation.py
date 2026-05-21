from pydantic import BaseModel, Field

from app.schemas.search import SearchHit


class RecommendationsResponse(BaseModel):
    note_id: str = Field(..., alias="noteId")
    related: list[SearchHit]

    model_config = {"populate_by_name": True}
