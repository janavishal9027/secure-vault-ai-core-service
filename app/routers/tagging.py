import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.tagging import TagsRequest, TagsResponse
from app.security import require_user
from app.services.tagging import generate_tags

router = APIRouter(prefix="/tags", tags=["tagging"])
log = logging.getLogger(__name__)


@router.post("", response_model=TagsResponse)
async def tags(
    request: TagsRequest,
    _user_id: str = Depends(require_user),
) -> TagsResponse:
    try:
        tag_list, model = await generate_tags(request.title, request.content)
    except Exception as exc:
        log.exception("tag generation failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"tagging failed: {exc}",
        ) from exc
    return TagsResponse(noteId=request.note_id, tags=tag_list, model=model)
