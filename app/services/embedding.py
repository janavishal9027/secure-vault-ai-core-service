from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chunking import split_into_chunks
from app.config import settings
from app.llm import embed_texts
from app.models import NoteEmbedding


async def index_note(
    session: AsyncSession,
    note_id: str,
    owner_user_id: str,
    title: str | None,
    content: str,
) -> int:
    chunks = split_into_chunks(content, settings.embed_chunk_size_chars) or [content]
    vectors = await embed_texts(chunks, task_type="RETRIEVAL_DOCUMENT")

    await session.execute(
        delete(NoteEmbedding).where(NoteEmbedding.note_id == note_id)
    )

    for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
        session.add(
            NoteEmbedding(
                note_id=note_id,
                owner_user_id=owner_user_id,
                chunk_index=idx,
                chunk_text=chunk,
                note_title=title,
                embedding=vector,
            )
        )

    await session.commit()
    return len(chunks)


async def delete_note_embeddings(session: AsyncSession, note_id: str) -> int:
    result = await session.execute(
        delete(NoteEmbedding).where(NoteEmbedding.note_id == note_id)
    )
    await session.commit()
    return result.rowcount or 0


async def fetch_first_chunk(session: AsyncSession, note_id: str) -> NoteEmbedding | None:
    result = await session.execute(
        select(NoteEmbedding)
        .where(NoteEmbedding.note_id == note_id, NoteEmbedding.chunk_index == 0)
        .limit(1)
    )
    return result.scalar_one_or_none()
