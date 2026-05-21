from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.search import SearchHit


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: str | None = Field(default=None, alias="conversationId")
    use_notes_context: bool = Field(default=False, alias="useNotesContext")

    model_config = {"populate_by_name": True}


class ChatResponse(BaseModel):
    conversation_id: str = Field(..., alias="conversationId")
    reply: str
    citations: list[SearchHit]
    model: str

    model_config = {"populate_by_name": True}


class ChatMessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime = Field(..., alias="createdAt")

    model_config = {"populate_by_name": True}


class ChatHistoryResponse(BaseModel):
    conversation_id: str = Field(..., alias="conversationId")
    messages: list[ChatMessageOut]

    model_config = {"populate_by_name": True}


class ChatConversationSummary(BaseModel):
    conversation_id: str = Field(..., alias="conversationId")
    title: str | None = None
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = {"populate_by_name": True}


class ChatConversationsListResponse(BaseModel):
    conversations: list[ChatConversationSummary]
