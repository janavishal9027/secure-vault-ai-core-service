import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.llm import chat_model_name, generate_with_history
from app.models import ChatConversation, ChatMessage
from app.schemas.chat import (
    ChatConversationSummary,
    ChatConversationsListResponse,
    ChatHistoryResponse,
    ChatMessageOut,
    ChatResponse,
)
from app.schemas.search import SearchHit
from app.services.search import search_by_query

CHAT_SYSTEM_PROMPT = (
    "You are a helpful assistant integrated with the user's personal notes. "
    "When relevant notes are provided as context, use them to answer accurately and cite them as [n]. "
    "If no relevant notes are available, answer from general knowledge but say so. "
    "Keep responses focused and conversational."
)


def _build_context_block(hits: list[SearchHit]) -> str:
    if not hits:
        return ""
    parts = []
    for i, hit in enumerate(hits, start=1):
        header = f"[{i}] {hit.title or 'Untitled note'} (noteId={hit.note_id})"
        parts.append(f"{header}\n{hit.chunk_text}")
    return "Relevant notes:\n" + "\n\n".join(parts) + "\n\n---\n\n"


async def _get_or_create_conversation(
    session: AsyncSession, owner_user_id: str, conversation_id: str | None
) -> ChatConversation:
    if conversation_id:
        existing = await session.get(ChatConversation, conversation_id)
        if existing and existing.owner_user_id == owner_user_id:
            return existing

    new = ChatConversation(
        conversation_id=uuid.uuid4().hex,
        owner_user_id=owner_user_id,
    )
    session.add(new)
    await session.flush()
    return new


async def _load_history(
    session: AsyncSession, conversation_id: str, limit: int
) -> list[tuple[str, str]]:
    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.id.desc())
        .limit(limit)
    )
    rows = list(reversed(result.scalars().all()))
    return [(m.role, m.content) for m in rows]


async def send_message(
    session: AsyncSession,
    owner_user_id: str,
    message: str,
    conversation_id: str | None,
    use_notes_context: bool,
) -> ChatResponse:
    conversation = await _get_or_create_conversation(
        session, owner_user_id, conversation_id
    )

    citations: list[SearchHit] = []
    if use_notes_context:
        citations = await search_by_query(
            session, owner_user_id, message, settings.search_default_top_k
        )

    history = await _load_history(
        session, conversation.conversation_id, settings.chat_history_window
    )

    augmented_message = _build_context_block(citations) + message
    reply = await generate_with_history(
        CHAT_SYSTEM_PROMPT, history, augmented_message, temperature=0.4
    )

    session.add(
        ChatMessage(
            conversation_id=conversation.conversation_id,
            role="user",
            content=message,
        )
    )
    session.add(
        ChatMessage(
            conversation_id=conversation.conversation_id,
            role="assistant",
            content=reply,
        )
    )

    if conversation.title is None and message:
        conversation.title = message[:80]

    await session.commit()

    return ChatResponse(
        conversationId=conversation.conversation_id,
        reply=reply,
        citations=citations,
        model=chat_model_name(),
    )


async def list_conversations(
    session: AsyncSession, owner_user_id: str
) -> ChatConversationsListResponse:
    result = await session.execute(
        select(ChatConversation)
        .where(ChatConversation.owner_user_id == owner_user_id)
        .order_by(ChatConversation.updated_at.desc())
    )
    conversations = [
        ChatConversationSummary(
            conversationId=c.conversation_id,
            title=c.title,
            createdAt=c.created_at,
            updatedAt=c.updated_at,
        )
        for c in result.scalars().all()
    ]
    return ChatConversationsListResponse(conversations=conversations)


async def get_history(
    session: AsyncSession, conversation_id: str, owner_user_id: str
) -> ChatHistoryResponse | None:
    conversation = await session.get(ChatConversation, conversation_id)
    if conversation is None or conversation.owner_user_id != owner_user_id:
        return None

    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.id.asc())
    )
    messages = [
        ChatMessageOut(role=m.role, content=m.content, createdAt=m.created_at)
        for m in result.scalars().all()
    ]
    return ChatHistoryResponse(
        conversationId=conversation_id, messages=messages
    )
