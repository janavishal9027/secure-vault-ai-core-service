from app import gemini, openai_client
from app.config import settings

_chat_module = openai_client if settings.chat_provider == "openai" else gemini
_embed_module = openai_client if settings.embed_provider == "openai" else gemini

generate = _chat_module.generate
generate_with_history = _chat_module.generate_with_history
embed_query = _embed_module.embed_query
embed_texts = _embed_module.embed_texts

__all__ = [
    "embed_query",
    "embed_texts",
    "generate",
    "generate_with_history",
    "chat_model_name",
    "embed_model_name",
]


def chat_model_name() -> str:
    if settings.chat_provider == "openai":
        return settings.openai_chat_model
    return settings.gemini_chat_model


def embed_model_name() -> str:
    if settings.embed_provider == "openai":
        return settings.openai_embed_model
    return settings.gemini_embed_model
