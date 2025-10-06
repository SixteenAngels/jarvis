from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Iterable, Tuple


@dataclass
class TextChunk:
    text: str
    metadata: Dict[str, Any]


def simple_tokenize(text: str, max_tokens: int = 256) -> List[str]:
    if not text:
        return []
    words = text.split()
    chunks: List[str] = []
    current: List[str] = []
    for word in words:
        current.append(word)
        if len(current) >= max_tokens:
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks


def chunk_text_overlap(text: str, metadata: Dict[str, Any], max_tokens: int = 256, overlap: int = 32) -> List[TextChunk]:
    if not text:
        return []
    words = text.split()
    chunks: List[TextChunk] = []
    start = 0
    while start < len(words):
        end = min(start + max_tokens, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(TextChunk(chunk, metadata))
        if end == len(words):
            break
        start = max(0, end - overlap)
    return chunks


def chunk_text(text: str, metadata: Dict[str, Any], max_tokens: int = 256) -> List[TextChunk]:
    return [TextChunk(t, metadata) for t in simple_tokenize(text, max_tokens=max_tokens)]


def l2_normalize(vector: List[float]) -> List[float]:
    import math

    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    return sum(a * b for a, b in zip(vec_a, vec_b))


class SimpleEmbedder:
    """Very small deterministic bag-of-words embedder for bootstrap/testing.

    This is intentionally simple so we can run unit tests without heavy deps.
    Replace later with SentenceTransformers or OpenAI embeddings.
    """

    def __init__(self) -> None:
        self.vocabulary: Dict[str, int] = {}

    def _get_index(self, token: str) -> int:
        if token not in self.vocabulary:
            self.vocabulary[token] = len(self.vocabulary)
        return self.vocabulary[token]

    def encode(self, texts: Iterable[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        for text in texts:
            # Build sparse count vector
            token_counts: Dict[int, float] = {}
            for token in text.lower().split():
                idx = self._get_index(token)
                token_counts[idx] = token_counts.get(idx, 0.0) + 1.0
            # Convert to dense vector
            size = len(self.vocabulary)
            dense = [0.0] * size
            for idx, count in token_counts.items():
                dense[idx] = count
            vectors.append(l2_normalize(dense))
        return vectors


def top_k_by_cosine(query_vec: List[float], docs: List[Tuple[str, List[float]]], k: int = 5) -> List[int]:
    sims = [cosine_similarity(query_vec, vec) for _, vec in docs]
    ranked = sorted(range(len(docs)), key=lambda i: sims[i], reverse=True)
    return ranked[:k]
