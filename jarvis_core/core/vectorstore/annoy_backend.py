from __future__ import annotations

from typing import List, Dict, Any, Tuple
from pathlib import Path
import json

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
        self._dim: int | None = None

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
        self._dim = dim
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

    # ---------------- Persistence -----------------
    @classmethod
    def load(cls, dir_path: str | Path) -> "AnnoyVectorIndex":
        dirp = Path(dir_path)
        idx_file = dirp / "index.ann"
        txt_file = dirp / "texts.jsonl"
        inst = cls()
        if not idx_file.exists() or not txt_file.exists():
            return inst
        # Load texts/metas first to get dim from embedder if needed
        texts: List[str] = []
        metas: List[Dict[str, Any]] = []
        with txt_file.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                obj = json.loads(line)
                texts.append(obj.get("text", ""))
                metas.append(obj.get("metadata", {}))
        # Re-embed to recover dimension (approximate)
        vecs = inst.embedder.encode(texts[:1])
        if not vecs:
            return inst
        dim = len(vecs[0])
        inst._ensure_index(dim)
        # Load index structure
        inst._index.load(str(idx_file))
        inst._texts = texts
        inst._metas = metas
        return inst

    def save(self, dir_path: str | Path) -> None:
        dirp = Path(dir_path)
        dirp.mkdir(parents=True, exist_ok=True)
        idx_file = dirp / "index.ann"
        txt_file = dirp / "texts.jsonl"
        if self._index is None:
            return
        self._index.save(str(idx_file))
        with txt_file.open("w", encoding="utf-8") as f:
            for t, m in zip(self._texts, self._metas):
                f.write(json.dumps({"text": t, "metadata": m}) + "\n")
