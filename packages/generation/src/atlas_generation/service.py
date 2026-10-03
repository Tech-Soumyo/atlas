"""Generation service with structured abstain output."""

from __future__ import annotations

from dataclasses import dataclass

from atlas_common.config import Settings, get_settings, get_yaml_config

from atlas_generation.abstain import abstain_answer, should_abstain
from atlas_generation.llm_client import chat_json
from atlas_generation.prompts.ask import SYSTEM_PROMPT, build_user_prompt


@dataclass(frozen=True)
class GenerationResult:
    answer: str
    abstained: bool
    model_name: str
    insufficient_context: bool


async def generate_answer(
    *,
    question: str,
    contexts: list[str],
    best_similarity: float | None,
    model: str | None = None,
    temperature: float | None = None,
    settings: Settings | None = None,
) -> GenerationResult:
    cfg = settings or get_settings()
    retrieval_cfg = get_yaml_config("retrieval", settings=cfg)
    min_score = float(retrieval_cfg.get("min_score", 0.25))
    model_name = model or cfg.llm_model

    if not contexts:
        return GenerationResult(
            answer=abstain_answer(),
            abstained=True,
            model_name=model_name,
            insufficient_context=True,
        )

    parsed = await chat_json(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(question, contexts)},
        ],
        model=model_name,
        temperature=temperature,
        settings=cfg,
    )
    insufficient = bool(parsed.get("insufficient_context", False))
    answer = str(parsed.get("answer", "")).strip()
    abstained = should_abstain(
        best_similarity=best_similarity,
        min_score=min_score,
        insufficient_context=insufficient,
    )
    if abstained:
        answer = abstain_answer()
    elif not answer:
        abstained = True
        answer = abstain_answer()
    return GenerationResult(
        answer=answer,
        abstained=abstained,
        model_name=model_name,
        insufficient_context=insufficient,
    )
