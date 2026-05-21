import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.chat import (
    ChatConversationsListResponse,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
)
from app.security import require_user
from app.services.chat import get_history, list_conversations, send_message

router = APIRouter(prefix="/chat", tags=["chat"])
log = logging.getLogger(__name__)


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    owner_user_id: str = Depends(require_user),
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    try:
        return await send_message(
            session,
            owner_user_id=owner_user_id,
            message=request.message,
            conversation_id=request.conversation_id,
            use_notes_context=request.use_notes_context,
        )
    except Exception as exc:
        log.exception("chat failed for user %s", owner_user_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"chat failed: {exc}",
        ) from exc


@router.get("/conversations", response_model=ChatConversationsListResponse)
async def chat_conversations(
    owner_user_id: str = Depends(require_user),
    session: AsyncSession = Depends(get_session),
) -> ChatConversationsListResponse:
    return await list_conversations(session, owner_user_id)


@router.get("/{conversation_id}/history", response_model=ChatHistoryResponse)
async def chat_history(
    conversation_id: str,
    owner_user_id: str = Depends(require_user),
    session: AsyncSession = Depends(get_session),
) -> ChatHistoryResponse:
    result = await get_history(session, conversation_id, owner_user_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conversation not found")
    return result
