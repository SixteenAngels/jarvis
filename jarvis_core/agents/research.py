from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List

from ..core.vectorstore.faiss_index import InMemoryVectorIndex
from ..core.vectorstore.persistent_index import PersistentVectorIndex
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

    def __init__(self, index: InMemoryVectorIndex | None = None, persist_dir: str | None = None) -> None:
        super().__init__()
        if index is not None:
            self.index = index
        elif persist_dir:
            self.index = PersistentVectorIndex.load(persist_dir)
            self._persist_dir = persist_dir
        else:
            self.index = InMemoryVectorIndex()
            self._persist_dir = None
        VECTOR_DIR.mkdir(parents=True, exist_ok=True)
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

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
        chunks = chunk_text(text, metadata={"source": str(file_path)})
        texts = [c.text for c in chunks]
        metas = [c.metadata for c in chunks]
        self.index.add_texts(texts, metas)
        # write meta.jsonl append-only
        with META_PATH.open("a", encoding="utf-8") as f:
            for meta in metas:
                f.write(json.dumps(meta) + "\n")
        return len(chunks)

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
            lines.append(f"{i}. [{score:.3f}] {src}: {doc.text[:160]}")
        return "\n".join(lines) if lines else "No results"
