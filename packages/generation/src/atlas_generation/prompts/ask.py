"""Ask prompt builders."""

from __future__ import annotations

SYSTEM_PROMPT = (
    "You answer questions using only the provided context chunks. "
    "Return JSON with keys answer (string) and insufficient_context (boolean). "
    "Set insufficient_context true when the context does not support a grounded answer. "
    "Do not invent facts outside the context."
)


def build_user_prompt(question: str, contexts: list[str]) -> str:
    joined = "\n\n---\n\n".join(
        f"[chunk {index + 1}]\n{text}" for index, text in enumerate(contexts)
    )
    return (
        f"Question:\n{question}\n\n"
        f"Context:\n{joined}\n\n"
        "Respond with JSON: "
        '{"answer": "...", "insufficient_context": true|false}'
    )
