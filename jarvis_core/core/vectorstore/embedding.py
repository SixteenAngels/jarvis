from __future__ import annotations

from typing import Iterable, List

from .utils import SimpleEmbedder, l2_normalize


class EmbeddingAdapter:
    """Adapter that uses sentence-transformers if available, else SimpleEmbedder.

    Exposes a single method encode(texts) -> List[List[float]].
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.backend_name: str
        self._st_model = None
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            try:
                self._st_model = SentenceTransformer(model_name)
                self.backend_name = "sentence_transformers"
            except Exception:
                self._st_model = None
                self.backend_name = "simple"
        except Exception:
            self.backend_name = "simple"
        self._simple = SimpleEmbedder()

    def encode(self, texts: Iterable[str]) -> List[List[float]]:
        texts_list = list(texts)
        if self._st_model is not None:
            vecs = self._st_model.encode(texts_list, normalize_embeddings=False, convert_to_numpy=False)  # type: ignore[attr-defined]
            # Ensure Python lists and normalized
            return [l2_normalize(list(map(float, v))) for v in vecs]
        # Fallback to simple embedder
        return self._simple.encode(texts_list)
