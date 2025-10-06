from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List

from ..core.vectorstore.faiss_index import InMemoryVectorIndex
from ..core.vectorstore.utils import chunk_text
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

    def __init__(self, index: InMemoryVectorIndex | None = None) -> None:
        super().__init__()
        self.index = index or InMemoryVectorIndex()
        VECTOR_DIR.mkdir(parents=True, exist_ok=True)
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # ----------------------- Public API -----------------------
    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        lower = task.lower().strip()
        if lower.startswith("ingest "):
            # Expect: "ingest <path>"
            path = lower.split(" ", 1)[1]
            res = self._ingest_path(Path(path))
            return {
                "status": "ok",
                "result": f"Ingested {res.num_chunks} chunks from {len(res.sources)} sources",
                "artifacts": [{"type": "meta", "path": str(META_PATH)}],
            }
        if lower.startswith("query ") or lower.startswith("ask ") or "retrieve" in lower:
            query = lower.split(" ", 1)[1] if " " in lower else lower
            hits = self.index.search(query, k=int(context.get("k", 5)))
            response = self._format_hits(hits)
            return {
                "status": "ok",
                "result": response,
                "artifacts": [],
            }
        # Fallback simple search
        hits = self.index.search(lower, k=int(context.get("k", 5)))
        response = self._format_hits(hits)
        return {"status": "ok", "result": response, "artifacts": []}

    # ----------------------- Helpers -------------------------
    def _ingest_path(self, path: Path) -> IngestResult:
        if path.is_dir():
            sources: List[str] = []
            total = 0
            for p in path.rglob("*"):
                if p.is_file() and p.suffix.lower() in {".txt", ".md"}:
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
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        chunks = chunk_text(text, metadata={"source": str(file_path)})
        texts = [c.text for c in chunks]
        metas = [c.metadata for c in chunks]
        self.index.add_texts(texts, metas)
        # write meta.jsonl append-only
        with META_PATH.open("a", encoding="utf-8") as f:
            for meta in metas:
                f.write(json.dumps(meta) + "\n")
        return len(chunks)

    def _format_hits(self, hits: List) -> str:
        lines: List[str] = []
        for i, (idx, score, doc) in enumerate(hits, 1):
            src = doc.metadata.get("source", "unknown")
            lines.append(f"{i}. [{score:.3f}] {src}: {doc.text[:160]}")
        return "\n".join(lines) if lines else "No results"
