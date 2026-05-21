from pydantic import BaseModel, Field


class TagsRequest(BaseModel):
    note_id: str | None = Field(default=None, alias="noteId")
    title: str | None = None
    content: str = Field(..., min_length=1)

    model_config = {"populate_by_name": True}


class TagsResponse(BaseModel):
    note_id: str | None = Field(default=None, alias="noteId")
    tags: list[str]
    model: str

    model_config = {"populate_by_name": True}
