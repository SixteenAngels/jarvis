from __future__ import annotations

import math
from typing import List


def _tokenize(text: str) -> List[str]:
    return [t for t in text.lower().split() if t]


def bm25_scores(query: str, docs: List[str], k1: float = 1.5, b: float = 0.75) -> List[float]:
    q_tokens = _tokenize(query)
    d_tokens = [ _tokenize(d) for d in docs ]
    N = len(docs)
    avgdl = sum(len(dt) for dt in d_tokens) / max(N, 1)
    # document frequencies
    df = {}
    for dt in d_tokens:
        seen = set(dt)
        for t in seen:
            df[t] = df.get(t, 0) + 1
    scores: List[float] = []
    for dt in d_tokens:
        score = 0.0
        dl = len(dt) or 1
        tf = {}
        for t in dt:
            tf[t] = tf.get(t, 0) + 1
        for t in q_tokens:
            if t not in df:
                continue
            idf = math.log( (N - df[t] + 0.5) / (df[t] + 0.5) + 1 )
            freq = tf.get(t, 0)
            denom = freq + k1 * (1 - b + b * dl / avgdl)
            score += idf * ( (freq * (k1 + 1)) / max(denom, 1e-9) )
        scores.append(score)
    return scores
