from __future__ import annotations

from typing import List, Dict, Any, Tuple

try:
    from annoy import AnnoyIndex  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    AnnoyIndex = None  # type: ignore

from .embedding import EmbeddingAdapter


class AnnoyVectorIndex:
    def __init__(self, embedder: EmbeddingAdapter | None = None, n_trees: int = 10) -> None:
        if AnnoyIndex is None:
            raise RuntimeError("annoy is not installed")
        self.embedder = embedder or EmbeddingAdapter()
        self._index = None
        self._texts: List[str] = []
        self._metas: List[Dict[str, Any]] = []
        self._n_trees = n_trees

    def _ensure_index(self, dim: int) -> None:
        if self._index is None:
            self._index = AnnoyIndex(dim, metric="angular")

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]] | None = None) -> List[int]:
        if metadatas is None:
            metadatas = [{} for _ in texts]
        vecs = self.embedder.encode(texts)
        if not vecs:
            return []
        dim = len(vecs[0])
        self._ensure_index(dim)
        ids: List[int] = []
        for offset, v in enumerate(vecs):
            idx = len(self._texts) + offset
            self._index.add_item(idx, v)
            ids.append(idx)
        self._index.build(self._n_trees)
        self._texts.extend(texts)
        self._metas.extend(metadatas)
        return ids

    def search(self, query: str, k: int = 5) -> List[Tuple[int, float, Any]]:
        if self._index is None:
            return []
        qv = self.embedder.encode([query])[0]
        idxs = self._index.get_nns_by_vector(qv, k, include_distances=True)
        results: List[Tuple[int, float, Any]] = []
        for idx, dist in zip(*idxs):
            score = max(0.0, 1.0 - float(dist))
            doc = type("Indexed", (), {"text": self._texts[idx], "metadata": self._metas[idx], "vector": qv})
            results.append((idx, score, doc))
        return results

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._texts)
