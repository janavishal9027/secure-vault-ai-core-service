from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.search import SearchHit
from app.services.embedding import fetch_first_chunk
from app.services.search import search_by_vector


async def recommend_related(
    session: AsyncSession,
    owner_user_id: str,
    note_id: str,
    top_k: int,
) -> list[SearchHit]:
    seed = await fetch_first_chunk(session, note_id)
    if seed is None:
        return []

    return await search_by_vector(
        session,
        owner_user_id=owner_user_id,
        vector=list(seed.embedding),
        top_k=top_k + 1,
        exclude_note_id=note_id,
    )
