import asyncio
import logging
from typing import Iterable

from openai import AsyncOpenAI

from app.config import settings

OPENAI_CALL_TIMEOUT_SECONDS = 60.0

log = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured. "
                "Set it in ai-core-service/.env."
            )

        # OpenRouter requires these optional headers; harmless on api.openai.com.
        default_headers = {}
        if "openrouter.ai" in settings.openai_base_url:
            default_headers["HTTP-Referer"] = "http://localhost:3000"
            default_headers["X-Title"] = settings.openai_app_title

        _client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=OPENAI_CALL_TIMEOUT_SECONDS,
            default_headers=default_headers or None,
        )
    return _client


class OpenAITimeoutError(RuntimeError):
    """Raised when an OpenAI call exceeds the per-call timeout."""


async def _with_timeout(coro, op: str):
    try:
        return await asyncio.wait_for(coro, timeout=OPENAI_CALL_TIMEOUT_SECONDS)
    except asyncio.TimeoutError as exc:
        log.error("OpenAI %s timed out after %.1fs", op, OPENAI_CALL_TIMEOUT_SECONDS)
        raise OpenAITimeoutError(
            f"OpenAI {op} did not respond within {OPENAI_CALL_TIMEOUT_SECONDS:.0f}s"
        ) from exc


async def embed_texts(
    texts: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> list[list[float]]:
    if not texts:
        return []

    response = await _with_timeout(
        _get_client().embeddings.create(
            model=settings.openai_embed_model,
            input=texts,
            dimensions=settings.embed_dimensions,
        ),
        op="embed",
    )
    return [list(item.embedding) for item in response.data]


async def embed_query(text: str) -> list[float]:
    embeddings = await embed_texts([text], task_type="RETRIEVAL_QUERY")
    return embeddings[0]


async def generate(
    system_instruction: str,
    user_content: str,
    temperature: float = 0.3,
) -> str:
    response = await _with_timeout(
        _get_client().chat.completions.create(
            model=settings.openai_chat_model,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content},
            ],
            temperature=temperature,
        ),
        op="generate",
    )
    return (response.choices[0].message.content or "").strip()


async def generate_with_history(
    system_instruction: str,
    history: Iterable[tuple[str, str]],
    user_message: str,
    temperature: float = 0.4,
) -> str:
    messages: list[dict] = [{"role": "system", "content": system_instruction}]
    for role, message in history:
        messages.append(
            {
                "role": "user" if role == "user" else "assistant",
                "content": message,
            }
        )
    messages.append({"role": "user", "content": user_message})

    response = await _with_timeout(
        _get_client().chat.completions.create(
            model=settings.openai_chat_model,
            messages=messages,
            temperature=temperature,
        ),
        op="generate_with_history",
    )
    return (response.choices[0].message.content or "").strip()
