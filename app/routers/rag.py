import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.schemas.rag import RagAnswerRequest, RagAnswerResponse
from app.services.rag import answer_question

router = APIRouter(prefix="/rag", tags=["rag"])
log = logging.getLogger(__name__)


@router.post("/answer", response_model=RagAnswerResponse)
async def rag_answer(
    request: RagAnswerRequest,
    session: AsyncSession = Depends(get_session),
) -> RagAnswerResponse:
    top_k = min(request.top_k or settings.search_default_top_k, settings.search_max_top_k)
    try:
        return await answer_question(session, request.owner_user_id, request.question, top_k)
    except Exception as exc:
        log.exception("RAG answer failed for user %s", request.owner_user_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"rag failed: {exc}",
        ) from exc
