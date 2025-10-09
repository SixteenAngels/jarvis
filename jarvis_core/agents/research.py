from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List

from ..core.vectorstore.faiss_index import InMemoryVectorIndex
from ..core.vectorstore.persistent_index import PersistentVectorIndex
from ..core.vectorstore.factory import get_index
from ..core.vectorstore.utils import chunk_text_overlap, cosine_similarity
from ..core.vectorstore.bm25 import bm25_scores
from ..core.vectorstore.cross_encoder import CrossEncoderReranker
from ..utils.config import load_yaml
import hashlib
from .base import BaseAgent


ARTIFACTS_DIR = Path("/workspace/data/artifacts")
VECTOR_DIR = Path("/workspace/data/vectorstore")
META_PATH = VECTOR_DIR / "meta.jsonl"


@dataclass
class IngestResult:
    num_chunks: int
    sources: List[str]


class ResearchAgent(BaseAgent):
    name: str = "research"
    intents: List[str] = [
        "ingest",
        "document",
        "pdf",
        "research",
        "summarize",
        "retrieve",
        "search",
        "rag",
    ]

    def __init__(self, index: InMemoryVectorIndex | None = None, persist_dir: str | None = None, backend: str = "memory") -> None:
        super().__init__()
        if index is not None:
            self.index = index
        elif persist_dir:
            backend_cfg = backend
            # Try to load from vectorstore.yaml if present
            try:
                from ..utils.config import load_yaml  # type: ignore
                cfg = load_yaml("/workspace/configs/vectorstore.yaml")
                backend_cfg = cfg.get("backend", backend_cfg)
            except Exception:
                pass
            self.index = get_index(backend=backend_cfg, persist_dir=persist_dir)
            self._persist_dir = persist_dir
        else:
            self.index = get_index(backend=backend)
            self._persist_dir = None
        VECTOR_DIR.mkdir(parents=True, exist_ok=True)
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        feats = load_yaml("/workspace/configs/features.yaml").get("features", {})
        self._cross = CrossEncoderReranker() if feats.get("cross_encoder", True) else CrossEncoderReranker("")

    # ----------------------- Public API -----------------------
    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        lower = task.lower().strip()
        if lower.startswith("ingest "):
            # Expect: "ingest <path>"
            path = lower.split(" ", 1)[1]
            res = self._ingest_path(Path(path))
            # Persist if enabled
            if getattr(self, '_persist_dir', None):
                # Save the augmented index
                assert isinstance(self.index, PersistentVectorIndex) or hasattr(self.index, 'save')
                try:
                    self.index.save(self._persist_dir)  # type: ignore[attr-defined]
                except Exception:
                    pass
            # Optional: re-embed entire index if feature enabled
            feats = load_yaml("/workspace/configs/features.yaml").get("features", {})
            if feats.get("reembed_on_ingest"):
                try:
                    self._reembed_index()
                    if getattr(self, '_persist_dir', None):
                        self.index.save(self._persist_dir)  # type: ignore[attr-defined]
                except Exception:
                    pass
            return {
                "status": "ok",
                "result": f"Ingested {res.num_chunks} chunks from {len(res.sources)} sources",
                "artifacts": [{"type": "meta", "path": str(META_PATH)}],
            }
        if lower.startswith("query ") or lower.startswith("ask ") or "retrieve" in lower:
            query = lower.split(" ", 1)[1] if " " in lower else lower
            k = int(context.get("k", 5))
            hits = self.index.search(query, k=k)
            # Simple MMR-like reranking for diversity
            try:
                qvec = self.index.embedder.encode([query])[0]
                hits = self._rerank_mmr(hits, qvec, k=k)
                # BM25 hybrid boost
                texts = [doc.text for (_, _, doc) in hits]
                bm = bm25_scores(query, texts)
                ce_order = self._cross.rerank(query, texts, bm)
                # reorder hits by cross-encoder order; sum scores for stability
                hits = [hits[j] for j in ce_order]
                hits = [ (i, score + 0.1*bm[j], doc) for j,(i,score,doc) in enumerate(hits) ]
            except Exception:
                pass
            response = self._format_hits(hits)
            return {
                "status": "ok",
                "result": response,
                "artifacts": [self._citations_from_hits(hits)],
            }
        # Fallback simple search
        k = int(context.get("k", 5))
        hits = self.index.search(lower, k=k)
        try:
            qvec = self.index.embedder.encode([lower])[0]
            hits = self._rerank_mmr(hits, qvec, k=k)
            texts = [doc.text for (_, _, doc) in hits]
            bm = bm25_scores(lower, texts)
            ce_order = self._cross.rerank(lower, texts, bm)
            hits = [hits[j] for j in ce_order]
            hits = [ (i, score + 0.1*bm[j], doc) for j,(i,score,doc) in enumerate(hits) ]
        except Exception:
            pass
        response = self._format_hits(hits)
        return {
            "status": "ok",
            "result": response,
            "artifacts": [self._citations_from_hits(hits)],
        }

    # ----------------------- Helpers -------------------------
    def _ingest_path(self, path: Path) -> IngestResult:
        if path.is_dir():
            sources: List[str] = []
            total = 0
            for p in path.rglob("*"):
                if p.is_file() and p.suffix.lower() in {".txt", ".md", ".pdf"}:
                    n = self._ingest_file(p)
                    total += n
                    sources.append(str(p))
            return IngestResult(num_chunks=total, sources=sources)
        else:
            n = self._ingest_file(path)
            return IngestResult(num_chunks=n, sources=[str(path)])

    def _ingest_file(self, file_path: Path) -> int:
        if not file_path.exists():
            raise FileNotFoundError(str(file_path))
        if file_path.suffix.lower() == ".pdf":
            text = self._extract_pdf_text(file_path)
        else:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        doc_id = hashlib.sha1(str(file_path).encode("utf-8")).hexdigest()[:16]
        base_meta = {"source": str(file_path), "doc_id": doc_id, "page": 1}
        chunks = chunk_text_overlap(text, metadata=base_meta, max_tokens=256, overlap=32)
        texts = [c.text for c in chunks]
        metas = []
        for idx, c in enumerate(chunks):
            m = dict(c.metadata)
            m["chunk_index"] = idx
            metas.append(m)
        self.index.add_texts(texts, metas)
        # write meta.jsonl append-only
        with META_PATH.open("a", encoding="utf-8") as f:
            for meta in metas:
                f.write(json.dumps(meta) + "\n")
        return len(chunks)

    def _reembed_index(self) -> None:
        """Rebuild vectors for all stored texts with current embedder.

        Supports InMemoryVectorIndex (_docs), FAISS/Annoy backends (_texts/_metas),
        and Persistent JSONL via meta loader.
        """
        texts: List[str] = []
        metas: List[Dict[str, Any]] = []
        # Try direct attributes
        if hasattr(self.index, "_docs"):
            try:
                for d in getattr(self.index, "_docs"):
                    texts.append(d.text)
                    metas.append(d.metadata)
            except Exception:
                pass
        elif hasattr(self.index, "_texts") and hasattr(self.index, "_metas"):
            try:
                texts = list(getattr(self.index, "_texts"))
                metas = list(getattr(self.index, "_metas"))
            except Exception:
                pass
        # Recreate index fresh
        backend = "memory"
        try:
            cfg = load_yaml("/workspace/configs/vectorstore.yaml")
            backend = cfg.get("backend", "memory")
        except Exception:
            pass
        self.index = get_index(backend=backend)
        if texts:
            self.index.add_texts(texts, metas)

    def _extract_pdf_text(self, file_path: Path) -> str:
        try:
            from pypdf import PdfReader  # type: ignore
        except Exception:
            return ""
        try:
            reader = PdfReader(str(file_path))
            texts: List[str] = []
            for page in reader.pages:
                t = page.extract_text() or ""
                if t:
                    texts.append(t)
            return "\n".join(texts)
        except Exception:
            return ""

    def _format_hits(self, hits: List) -> str:
        lines: List[str] = []
        for i, (idx, score, doc) in enumerate(hits, 1):
            src = doc.metadata.get("source", "unknown")
            anchor = doc.text[:30].replace("\n", " ")
            lines.append(f"{i}. [{score:.3f}] {src} — ‘{anchor}…’")
        return "\n".join(lines) if lines else "No results"

    def _rerank_mmr(self, hits: List, query_vec: List[float], k: int = 5, lambda_param: float = 0.7) -> List:
        if not hits:
            return hits
        selected: List[int] = []
        candidates = list(range(len(hits)))
        # Precompute query sims from hits (second item of tuple)
        query_sims = [score for (_, score, _) in hits]
        # First select highest query sim
        best_first = max(candidates, key=lambda i: query_sims[i])
        selected.append(best_first)
        candidates.remove(best_first)
        while len(selected) < min(k, len(hits)) and candidates:
            def mmr_score(i: int) -> float:
                # diversity penalty: max sim to already selected
                max_sim = 0.0
                for s in selected:
                    doc_i = hits[i][2]
                    doc_s = hits[s][2]
                    sim = cosine_similarity(doc_i.vector, doc_s.vector)
                    if sim > max_sim:
                        max_sim = sim
                return lambda_param * query_sims[i] - (1 - lambda_param) * max_sim

            next_best = max(candidates, key=mmr_score)
            selected.append(next_best)
            candidates.remove(next_best)
        # Build new list preserving selected order
        return [hits[i] for i in selected]

    def _citations_from_hits(self, hits: List) -> Dict[str, Any]:
        # Deduplicate citations by source, keeping max score
        by_source: Dict[str, float] = {}
        for (_, score, doc) in hits:
            src = doc.metadata.get("source", "unknown")
            prev = by_source.get(src)
            if prev is None or score > prev:
                by_source[src] = score
        items = []
        for src, sc in by_source.items():
            # Find one matching doc to extract provenance
            prov = next(((doc, s) for (_, s, doc) in hits if doc.metadata.get("source", "unknown") == src and abs(s - sc) < 1e-6), None)
            snippet = ""
            meta: Dict[str, Any] = {"source": src, "score": sc}
            if prov:
                d, _ = prov
                snippet = d.text[:120]
                # Merge provenance anchors if present
                for key in ("doc_id", "page", "chunk_index", "start", "end"):
                    if key in d.metadata:
                        meta[key] = d.metadata[key]
            meta["snippet"] = snippet
            items.append(meta)
        items.sort(key=lambda x: x["score"], reverse=True)
        return {"type": "citations", "items": items}
