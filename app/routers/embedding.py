import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.llm import embed_model_name
from app.schemas.embedding import EmbedRequest, EmbedResponse
from app.services.embedding import delete_note_embeddings, index_note

router = APIRouter(prefix="/embed", tags=["embedding"])
log = logging.getLogger(__name__)


@router.post("", response_model=EmbedResponse)
async def embed_note(
    request: EmbedRequest,
    session: AsyncSession = Depends(get_session),
) -> EmbedResponse:
    try:
        chunks = await index_note(
            session,
            note_id=request.note_id,
            owner_user_id=request.owner_user_id,
            title=request.title,
            content=request.content,
        )
    except Exception as exc:
        log.exception("embedding failed for note %s", request.note_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"embedding failed: {exc}",
        ) from exc

    return EmbedResponse(
        noteId=request.note_id,
        chunksIndexed=chunks,
        embeddingModel=embed_model_name(),
    )


@router.delete("/{note_id}")
async def delete_embeddings(
    note_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    deleted = await delete_note_embeddings(session, note_id)
    return {"noteId": note_id, "deleted": deleted}
