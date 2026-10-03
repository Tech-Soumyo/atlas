"""OpenAI compatible chat client (Groq / Gemini / Ollama)."""

from __future__ import annotations

import json
from typing import Any, cast

from atlas_common.config import Settings, get_settings
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam


class LlmError(RuntimeError):
    """Provider or parse failure on the ask path."""


def build_client(settings: Settings | None = None) -> AsyncOpenAI:
    cfg = settings or get_settings()
    api_key = cfg.openai_api_key or "missing"
    return AsyncOpenAI(
        api_key=api_key,
        base_url=cfg.llm_base_url,
        timeout=cfg.llm_timeout_seconds,
        max_retries=cfg.llm_max_retries,
    )


async def chat_json(
    *,
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    cfg = settings or get_settings()
    if not cfg.openai_api_key and not cfg.is_test:
        raise LlmError("OPENAI_API_KEY is not configured")
    client = build_client(cfg)
    try:
        typed_messages = cast(list[ChatCompletionMessageParam], messages)
        response = await client.chat.completions.create(
            model=model or cfg.llm_model,
            temperature=cfg.llm_temperature if temperature is None else temperature,
            messages=typed_messages,
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        raise LlmError(str(exc)) from exc
    content = response.choices[0].message.content or "{}"
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise LlmError("LLM returned non JSON content") from exc
    if not isinstance(parsed, dict):
        raise LlmError("LLM JSON root must be an object")
    return parsed
