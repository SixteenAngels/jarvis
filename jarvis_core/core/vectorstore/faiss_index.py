from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

from .utils import SimpleEmbedder, top_k_by_cosine
from .embedding import EmbeddingAdapter


@dataclass
class IndexedChunk:
    text: str
    metadata: Dict[str, Any]
    vector: List[float]


class InMemoryVectorIndex:
    """Lightweight in-memory vector index to bootstrap RAG.

    Provides an FAISS-like interface for unit tests and development without
    heavyweight native dependencies.
    """

    def __init__(self, embedder: SimpleEmbedder | EmbeddingAdapter | None = None) -> None:
        # Prefer EmbeddingAdapter if none provided
        self.embedder = embedder or EmbeddingAdapter()
        self._docs: List[IndexedChunk] = []

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]] | None = None) -> List[int]:
        if metadatas is None:
            metadatas = [{} for _ in texts]
        vectors = self.embedder.encode(texts)
        ids: List[int] = []
        for text, metadata, vector in zip(texts, metadatas, vectors):
            self._docs.append(IndexedChunk(text=text, metadata=metadata, vector=vector))
            ids.append(len(self._docs) - 1)
        return ids

    def search(self, query: str, k: int = 5) -> List[Tuple[int, float, IndexedChunk]]:
        query_vec = self.embedder.encode([query])[0]
        doc_pairs = [(doc.text, doc.vector) for doc in self._docs]
        idxs = top_k_by_cosine(query_vec, doc_pairs, k=k)
        results: List[Tuple[int, float, IndexedChunk]] = []
        for i in idxs:
            doc = self._docs[i]
            # cosine_similarity equals dot product due to normalization
            score = sum(a * b for a, b in zip(query_vec, doc.vector))
            results.append((i, score, doc))
        return results

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._docs)
