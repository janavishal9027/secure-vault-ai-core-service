import asyncio
import logging
from typing import Iterable

from google import genai
from google.genai import types

from app.config import settings

GEMINI_CALL_TIMEOUT_SECONDS = 30.0

log = logging.getLogger(__name__)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. "
                "Either set it in ai-core-service/.env, or switch the provider "
                "(CHAT_PROVIDER / EMBED_PROVIDER) away from 'gemini'."
            )
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


class GeminiTimeoutError(RuntimeError):
    """Raised when a Gemini call exceeds the per-call timeout."""


async def _with_timeout(coro, op: str):
    try:
        return await asyncio.wait_for(coro, timeout=GEMINI_CALL_TIMEOUT_SECONDS)
    except asyncio.TimeoutError as exc:
        log.error("Gemini %s timed out after %.1fs", op, GEMINI_CALL_TIMEOUT_SECONDS)
        raise GeminiTimeoutError(
            f"Gemini {op} did not respond within {GEMINI_CALL_TIMEOUT_SECONDS:.0f}s"
        ) from exc


async def embed_texts(
    texts: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> list[list[float]]:
    if not texts:
        return []

    async def embed_one(text: str) -> list[float]:
        result = await _with_timeout(
            _get_client().aio.models.embed_content(
                model=settings.gemini_embed_model,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=settings.embed_dimensions,
                ),
            ),
            op="embed",
        )
        return list(result.embeddings[0].values)

    semaphore = asyncio.Semaphore(5)

    async def bounded(t: str) -> list[float]:
        async with semaphore:
            return await embed_one(t)

    return await asyncio.gather(*(bounded(t) for t in texts))


async def embed_query(text: str) -> list[float]:
    embeddings = await embed_texts([text], task_type="RETRIEVAL_QUERY")
    return embeddings[0]


async def generate(
    system_instruction: str,
    user_content: str,
    temperature: float = 0.3,
) -> str:
    response = await _with_timeout(
        _get_client().aio.models.generate_content(
            model=settings.gemini_chat_model,
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=temperature,
            ),
        ),
        op="generate",
    )
    return (response.text or "").strip()


async def generate_with_history(
    system_instruction: str,
    history: Iterable[tuple[str, str]],
    user_message: str,
    temperature: float = 0.4,
) -> str:
    contents: list[types.Content] = []
    for role, message in history:
        contents.append(
            types.Content(
                role="user" if role == "user" else "model",
                parts=[types.Part.from_text(text=message)],
            )
        )
    contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=user_message)])
    )

    response = await _with_timeout(
        _get_client().aio.models.generate_content(
            model=settings.gemini_chat_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=temperature,
            ),
        ),
        op="generate_with_history",
    )
    return (response.text or "").strip()
