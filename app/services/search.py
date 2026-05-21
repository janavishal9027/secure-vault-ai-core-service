from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm import embed_query
from app.models import NoteEmbedding
from app.schemas.search import SearchHit


async def search_by_query(
    session: AsyncSession,
    owner_user_id: str,
    query: str,
    top_k: int,
) -> list[SearchHit]:
    vector = await embed_query(query)
    return await search_by_vector(session, owner_user_id, vector, top_k)


async def search_by_vector(
    session: AsyncSession,
    owner_user_id: str,
    vector: list[float],
    top_k: int,
    exclude_note_id: str | None = None,
) -> list[SearchHit]:
    distance = NoteEmbedding.embedding.cosine_distance(vector)

    stmt = (
        select(NoteEmbedding, distance.label("distance"))
        .where(NoteEmbedding.owner_user_id == owner_user_id)
        .order_by(distance.asc())
        .limit(top_k)
    )
    if exclude_note_id:
        stmt = stmt.where(NoteEmbedding.note_id != exclude_note_id)

    result = await session.execute(stmt)

    hits: list[SearchHit] = []
    seen: set[str] = set()
    for row in result.all():
        note: NoteEmbedding = row[0]
        if note.note_id in seen:
            continue
        seen.add(note.note_id)
        score = max(0.0, 1.0 - float(row.distance))
        hits.append(
            SearchHit(
                noteId=note.note_id,
                title=note.note_title,
                chunkText=note.chunk_text,
                score=round(score, 4),
            )
        )
    return hits
