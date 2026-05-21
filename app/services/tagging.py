import re

from app.llm import chat_model_name, generate

TAGGING_SYSTEM_PROMPT = (
    "You generate 3-7 concise tags for a personal note. "
    "Tags must be lowercase, hyphenated when multi-word, technology/topic-oriented when applicable. "
    "Return ONLY a comma-separated list of tags, no explanations, no quotes, no preamble."
)


def _parse_tags(raw: str, max_tags: int = 7) -> list[str]:
    candidates = re.split(r"[,\n]+", raw)
    tags: list[str] = []
    seen: set[str] = set()
    for c in candidates:
        tag = c.strip().strip(".#").lower()
        tag = re.sub(r"\s+", "-", tag)
        if not tag or tag in seen:
            continue
        seen.add(tag)
        tags.append(tag)
        if len(tags) >= max_tags:
            break
    return tags


async def generate_tags(title: str | None, content: str) -> tuple[list[str], str]:
    user_prompt = (
        f"Title: {title}\n\nContent:\n{content}" if title else f"Content:\n{content}"
    )
    raw = await generate(TAGGING_SYSTEM_PROMPT, user_prompt, temperature=0.2)
    return _parse_tags(raw), chat_model_name()
