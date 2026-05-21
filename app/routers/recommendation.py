import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.schemas.recommendation import RecommendationsResponse
from app.security import require_user
from app.services.recommendation import recommend_related

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
log = logging.getLogger(__name__)


@router.get("/{note_id}", response_model=RecommendationsResponse)
async def recommendations(
    note_id: str,
    top_k: int | None = Query(default=None, alias="topK", ge=1, le=50),
    owner_user_id: str = Depends(require_user),
    session: AsyncSession = Depends(get_session),
) -> RecommendationsResponse:
    k = min(top_k or settings.search_default_top_k, settings.search_max_top_k)
    try:
        related = await recommend_related(session, owner_user_id, note_id, k)
    except Exception as exc:
        log.exception("recommendation failed for note %s", note_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"recommendation failed: {exc}",
        ) from exc
    return RecommendationsResponse(noteId=note_id, related=related)
