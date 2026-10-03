"""Local sentence-transformers embedder."""

from __future__ import annotations

from functools import lru_cache

from atlas_common.config import Settings, get_settings


class Embedder:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._model = _load_model(
            self._settings.embedding_model,
            self._settings.embedding_device,
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [list(map(float, row)) for row in vectors]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


@lru_cache(maxsize=2)
def _load_model(model_name: str, device: str) -> object:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name, device=device)
