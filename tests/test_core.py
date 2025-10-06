from __future__ import annotations

from pathlib import Path

from jarvis_core.core.kernel import Kernel
from jarvis_core.core.memory.short_term import ShortTermMemory
from jarvis_core.core.memory.long_term import LongTermMemory


def test_kernel_blocks_dangerous() -> None:
    k = Kernel()
    r = k.handle("please rm -rf /", {})
    assert r["status"] == "blocked"


def test_kernel_basic_flow(tmp_path: Path) -> None:
    # Use a temp persist dir for long-term memory
    k = Kernel(persist_dir=str(tmp_path))
    doc = tmp_path / "doc.txt"
    doc.write_text("Kernel test document for RAG.")
    # Ingest via research agent through kernel plan
    r1 = k.handle(f"ingest {doc}")
    assert r1["status"] == "ok"
    # Query to trigger RAG
    r2 = k.handle("query kernel document")
    assert r2["status"] == "ok"


def test_short_and_long_term_memory(tmp_path: Path) -> None:
    stm = ShortTermMemory(max_items=2)
    stm.add("a"); stm.add("b"); stm.add("c")
    assert stm.get() == ["b", "c"]

    ltm = LongTermMemory(tmp_path)
    ltm.add_document("hello world", source="test")
    ltm.save()
    hits = ltm.search("hello", k=1)
    assert hits and "hello" in hits[0]
