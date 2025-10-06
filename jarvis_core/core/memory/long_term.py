from __future__ import annotations

from pathlib import Path
from typing import List

from ..vectorstore.persistent_index import PersistentVectorIndex


class LongTermMemory:
    def __init__(self, dir_path: str | Path) -> None:
        self.dir = Path(dir_path)
        self.index = PersistentVectorIndex.load(self.dir)

    def add_document(self, text: str, source: str = "memory") -> None:
        self.index.append([text], [{"source": source}])

    def save(self) -> None:
        self.index.save(self.dir)

    def search(self, query: str, k: int = 5) -> List[str]:
        hits = self.index.search(query, k=k)
        return [doc.text for (_, _, doc) in hits]
