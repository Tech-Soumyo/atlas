"""Generate node for the linear ask graph."""

from __future__ import annotations

from typing import Any

from atlas_common.config import get_settings
from atlas_generation.service import generate_answer

from atlas_orchestration.state import AskState


async def generate_node(state: AskState) -> dict[str, Any]:
    settings = get_settings()
    result = await generate_answer(
        question=state["question"],
        contexts=list(state.get("contexts") or []),
        best_similarity=state.get("best_similarity"),
        model=state.get("model"),
        temperature=state.get("temperature"),
        settings=settings,
    )
    return {
        "answer": result.answer,
        "abstained": result.abstained,
        "model_name": result.model_name,
    }
