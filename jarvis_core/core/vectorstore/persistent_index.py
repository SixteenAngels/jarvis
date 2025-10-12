from __future__ import annotations

import json
from pathlib import Path
import shutil
import time
from contextlib import contextmanager
from typing import Dict, Any, List, Iterable

from .faiss_index import InMemoryVectorIndex


INDEX_FILENAME = "index.jsonl"
META_FILENAME = "meta.json"


class PersistentVectorIndex(InMemoryVectorIndex):
    """Persistence wrapper for InMemoryVectorIndex using JSONL.

    On save(): writes all chunks (text + metadata) to index.jsonl
    On load(): re-embeds chunks deterministically using the SimpleEmbedder.
    """

    def __init__(self) -> None:
        super().__init__()
        self._persist_dir: Path | None = None

    @staticmethod
    def _index_path(dir_path: Path) -> Path:
        return dir_path / INDEX_FILENAME

    @classmethod
    def load(cls, dir_path: str | Path) -> "PersistentVectorIndex":
        dirp = Path(dir_path)
        dirp.mkdir(parents=True, exist_ok=True)
        idx_path = cls._index_path(dirp)

        inst = cls()
        inst._persist_dir = dirp
        if not idx_path.exists():
            return inst

        texts: List[str] = []
        metas: List[Dict[str, Any]] = []
        with idx_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    texts.append(obj.get("text", ""))
                    metas.append(obj.get("metadata", {}))
                except json.JSONDecodeError:
                    continue
        if texts:
            inst.add_texts(texts, metas)
        return inst

    def save(self, dir_path: str | Path) -> None:
        dirp = Path(dir_path)
        dirp.mkdir(parents=True, exist_ok=True)
        idx_path = self._index_path(dirp)
        # backup existing file
        if idx_path.exists():
            ts = int(time.time())
            backup = idx_path.parent / f"{idx_path.name}.bak.{ts}"
            shutil.copy2(idx_path, backup)
        with self._file_lock(dirp):
            with idx_path.open("w", encoding="utf-8") as f:
                for doc in self._docs:
                    f.write(json.dumps({"text": doc.text, "metadata": doc.metadata}) + "\n")
        self._persist_dir = dirp

    def append(self, texts: Iterable[str], metadatas: Iterable[Dict[str, Any]]) -> None:
        # Add to memory and append to file for durability
        self.add_texts(list(texts), list(metadatas))
        if not self._persist_dir:
            return
        idx_path = self._index_path(self._persist_dir)
        with self._file_lock(self._persist_dir):
            with idx_path.open("a", encoding="utf-8") as f:
                for text, meta in zip(texts, metadatas):
                    f.write(json.dumps({"text": text, "metadata": meta}) + "\n")

    @contextmanager
    def _file_lock(self, dirp: Path):
        lock = dirp / ".lock"
        try:
            while lock.exists():
                time.sleep(0.05)
            lock.touch(exist_ok=False)
            yield
        finally:
            if lock.exists():
                lock.unlink()
