from __future__ import annotations

from typing import List

try:
    from sentence_transformers import CrossEncoder  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    CrossEncoder = None  # type: ignore


class CrossEncoderReranker:
    """Thin wrapper for a cross-encoder reranker.

    If sentence-transformers cross-encoder is unavailable, this class falls back
    to a no-op rerank that returns the input ordering.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        self.model = None
        if CrossEncoder is not None:
            try:
                self.model = CrossEncoder(model_name)
            except Exception:
                self.model = None

    def rerank(self, query: str, docs: List[str], scores: List[float]) -> List[int]:
        if not self.model:
            return list(range(len(docs)))
        pairs = [[query, d] for d in docs]
        ce = self.model.predict(pairs)  # type: ignore[attr-defined]
        # Combine with initial scores (simple sum)
        final = [(i, float(scores[i]) + float(ce[i])) for i in range(len(docs))]
        final.sort(key=lambda x: x[1], reverse=True)
        return [i for i, _ in final]
