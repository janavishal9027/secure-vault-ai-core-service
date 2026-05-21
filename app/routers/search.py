import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.schemas.search import SearchResponse
from app.security import require_user
from app.services.search import search_by_query

router = APIRouter(prefix="/search", tags=["search"])
log = logging.getLogger(__name__)


@router.get("", response_model=SearchResponse)
async def semantic_search(
    q: str = Query(..., min_length=1),
    top_k: int | None = Query(default=None, alias="topK", ge=1, le=50),
    owner_user_id: str = Depends(require_user),
    session: AsyncSession = Depends(get_session),
) -> SearchResponse:
    capped_top_k = min(top_k or settings.search_default_top_k, settings.search_max_top_k)
    try:
        hits = await search_by_query(session, owner_user_id, q, capped_top_k)
    except Exception as exc:
        log.exception("semantic search failed for user %s", owner_user_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"search failed: {exc}",
        ) from exc

    return SearchResponse(query=q, hits=hits)
