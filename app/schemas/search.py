from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    owner_user_id: str = Field(..., alias="ownerUserId")
    query: str = Field(..., min_length=1)
    top_k: int | None = Field(default=None, alias="topK", ge=1, le=50)

    model_config = {"populate_by_name": True}


class SearchHit(BaseModel):
    note_id: str = Field(..., alias="noteId")
    title: str | None = None
    chunk_text: str = Field(..., alias="chunkText")
    score: float

    model_config = {"populate_by_name": True}


class SearchResponse(BaseModel):
    query: str
    hits: list[SearchHit]
