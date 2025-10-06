from __future__ import annotations

from pathlib import Path
from typing import Optional

from .faiss_index import InMemoryVectorIndex
from .persistent_index import PersistentVectorIndex


def get_index(backend: str = "memory", persist_dir: Optional[str] = None):
    backend = (backend or "memory").lower()
    if persist_dir:
        # For simplicity, persistent index uses JSONL regardless of backend here
        try:
            return PersistentVectorIndex.load(persist_dir)
        except Exception:
            return PersistentVectorIndex()
    if backend == "faiss":
        try:
            import faiss  # type: ignore  # noqa: F401
            # Placeholder: would build a real FAISS index wrapper
            return InMemoryVectorIndex()
        except Exception:
            return InMemoryVectorIndex()
    if backend == "annoy":
        try:
            import annoy  # type: ignore  # noqa: F401
            # Placeholder: would build a real Annoy index wrapper
            return InMemoryVectorIndex()
        except Exception:
            return InMemoryVectorIndex()
    return InMemoryVectorIndex()
