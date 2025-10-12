from __future__ import annotations

from pathlib import Path

from jarvis_core.core.vectorstore.utils import chunk_text_overlap
from jarvis_core.core.vectorstore.persistent_index import PersistentVectorIndex
from jarvis_core.execution.action_manager import ActionManager
from jarvis_core.models.selector import ModelSelector


def test_chunk_overlap() -> None:
    text = " ".join(["word"] * 600)
    chunks = chunk_text_overlap(text, {"source": "t"}, max_tokens=100, overlap=20)
    assert len(chunks) >= 6
    # ensure overlap
    assert chunks[0].text.split()[-20:] == chunks[1].text.split()[:20]


def test_persistence_backup_and_lock(tmp_path: Path) -> None:
    idx = PersistentVectorIndex()
    idx.add_texts(["a b c"], [{"source": "s"}])
    idx.save(tmp_path)
    # second save creates backup
    idx.save(tmp_path)
    backups = list(tmp_path.glob("index.jsonl.bak.*"))
    assert backups, "Expected backup files to exist"


def test_action_manager_approvals(tmp_path: Path) -> None:
    am = ActionManager()
    r1 = am.request("block_ip", {"ip": "1.2.3.4"})
    assert r1.status == "ok"
    r2 = am.request("isolate_host", {"host": "x"})
    assert r2.status == "requires_approval"


def test_model_selector_backoff() -> None:
    ms = ModelSelector()
    out = ms.generate("hello")
    assert isinstance(out, str) and len(out) > 0
