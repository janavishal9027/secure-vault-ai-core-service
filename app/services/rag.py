from sqlalchemy.ext.asyncio import AsyncSession

from app.llm import chat_model_name, generate
from app.schemas.rag import RagAnswerResponse
from app.schemas.search import SearchHit
from app.services.search import search_by_query

RAG_SYSTEM_PROMPT = (
    "You answer questions using ONLY the user's personal notes provided as context. "
    "Cite sources inline as [n] matching the section numbers. "
    "If the notes don't contain the answer, say so plainly. "
    "Be concise (3-6 sentences unless the question demands more)."
)


def _build_context_block(hits: list[SearchHit]) -> str:
    parts: list[str] = []
    for i, hit in enumerate(hits, start=1):
        header = f"[{i}] {hit.title or 'Untitled note'} (noteId={hit.note_id})"
        parts.append(f"{header}\n{hit.chunk_text}")
    return "\n\n".join(parts)


async def answer_question(
    session: AsyncSession,
    owner_user_id: str,
    question: str,
    top_k: int,
) -> RagAnswerResponse:
    hits = await search_by_query(session, owner_user_id, question, top_k)

    if not hits:
        return RagAnswerResponse(
            question=question,
            answer=(
                "I couldn't find anything relevant in your notes. "
                "Try saving more notes on this topic, or rephrase your question."
            ),
            citations=[],
            model=chat_model_name(),
        )

    context = _build_context_block(hits)
    user_prompt = f"Notes:\n{context}\n\nQuestion: {question}"
    answer = await generate(RAG_SYSTEM_PROMPT, user_prompt, temperature=0.3)

    return RagAnswerResponse(
        question=question,
        answer=answer,
        citations=hits,
        model=chat_model_name(),
    )
