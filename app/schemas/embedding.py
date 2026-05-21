from pydantic import BaseModel, Field


class EmbedRequest(BaseModel):
    note_id: str = Field(..., alias="noteId")
    owner_user_id: str = Field(..., alias="ownerUserId")
    title: str | None = None
    content: str = Field(..., min_length=1)

    model_config = {"populate_by_name": True}


class EmbedResponse(BaseModel):
    note_id: str = Field(..., alias="noteId")
    chunks_indexed: int = Field(..., alias="chunksIndexed")
    embedding_model: str = Field(..., alias="embeddingModel")

    model_config = {"populate_by_name": True}
