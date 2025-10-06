from __future__ import annotations

from pathlib import Path
from typing import Optional

from .faiss_index import InMemoryVectorIndex
from .persistent_index import PersistentVectorIndex
from .faiss_backend import FaissVectorIndex
from .annoy_backend import AnnoyVectorIndex


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
            return FaissVectorIndex()
        except Exception:
            return InMemoryVectorIndex()
    if backend == "annoy":
        try:
            return AnnoyVectorIndex()
        except Exception:
            return InMemoryVectorIndex()
    return InMemoryVectorIndex()
