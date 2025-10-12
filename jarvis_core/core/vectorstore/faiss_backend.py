from __future__ import annotations

from typing import List, Dict, Any, Tuple
from pathlib import Path
import json

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    faiss = None  # type: ignore

from .embedding import EmbeddingAdapter


class FaissVectorIndex:
    """FAISS inner-product index with L2-normalized embeddings.

    Falls back to raise if faiss is unavailable at runtime.
    """

    def __init__(self, embedder: EmbeddingAdapter | None = None) -> None:
        if faiss is None:
            raise RuntimeError("faiss is not installed")
        self.embedder = embedder or EmbeddingAdapter()
        # Build once we know dimension
        self._index = None  # type: ignore
        self._texts: List[str] = []
        self._metas: List[Dict[str, Any]] = []
        self._dim: int | None = None

    def _ensure_index(self, dim: int) -> None:
        if self._index is None:
            self._index = faiss.IndexFlatIP(dim)  # cosine via normalized vectors

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]] | None = None) -> List[int]:
        if metadatas is None:
            metadatas = [{} for _ in texts]
        vecs = self.embedder.encode(texts)
        if not vecs:
            return []
        dim = len(vecs[0])
        self._dim = dim
        self._ensure_index(dim)
        import numpy as np

        xb = np.array(vecs, dtype="float32")
        self._index.add(xb)
        ids = list(range(len(self._texts), len(self._texts) + len(texts)))
        self._texts.extend(texts)
        self._metas.extend(metadatas)
        return ids

    # Alias for API parity with other indexes
    append = add_texts

    def search(self, query: str, k: int = 5) -> List[Tuple[int, float, Any]]:
        import numpy as np

        qv = self.embedder.encode([query])[0]
        xq = np.array([qv], dtype="float32")
        if self._index is None:
            return []
        D, I = self._index.search(xq, k)
        results: List[Tuple[int, float, Any]] = []
        for score, idx in zip(D[0], I[0]):
            if idx < 0:
                continue
            doc = type("Indexed", (), {"text": self._texts[idx], "metadata": self._metas[idx], "vector": qv})  # simple struct
            results.append((idx, float(score), doc))
        return results

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._texts)

    # ---------------- Persistence -----------------
    @classmethod
    def load(cls, dir_path: str | Path) -> "FaissVectorIndex":
        dirp = Path(dir_path)
        idx_file = dirp / "index.faiss"
        txt_file = dirp / "texts.jsonl"
        inst = cls()
        if not idx_file.exists() or not txt_file.exists():
            return inst
        # Load index
        inst._index = faiss.read_index(str(idx_file))
        # Load texts/metas
        with txt_file.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                obj = json.loads(line)
                inst._texts.append(obj.get("text", ""))
                inst._metas.append(obj.get("metadata", {}))
        return inst

    def save(self, dir_path: str | Path) -> None:
        dirp = Path(dir_path)
        dirp.mkdir(parents=True, exist_ok=True)
        idx_file = dirp / "index.faiss"
        txt_file = dirp / "texts.jsonl"
        if self._index is None:
            return
        faiss.write_index(self._index, str(idx_file))
        with txt_file.open("w", encoding="utf-8") as f:
            for t, m in zip(self._texts, self._metas):
                f.write(json.dumps({"text": t, "metadata": m}) + "\n")
