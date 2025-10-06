from __future__ import annotations

from pathlib import Path
import json

from jarvis_core.core.vectorstore.meta_loader import read_meta_lines, unique_sources
from jarvis_core.core.router import Router
from jarvis_core.core.kernel import Kernel
from jarvis_core.core.policy import Policy


def test_meta_loader_reads(tmp_path: Path) -> None:
    meta = tmp_path / "meta.jsonl"
    meta.write_text("\n".join([json.dumps({"source": "a"}), json.dumps({"source": "b"})]))
    recs = read_meta_lines(meta)
    assert set(unique_sources(recs)) == {"a", "b"}


def test_router_corrections(tmp_path: Path) -> None:
    r = Router()
    r.record_correction("task1", "agentX")
    p = Path("/workspace/data/router_corrections.json")
    assert p.exists()
    data = json.loads(p.read_text())
    assert any(d.get("task") == "task1" for d in data)


def test_kernel_logging_and_policy_emergency(tmp_path: Path) -> None:
    # emergency policies block shutdown
    (Path("/workspace/configs")).mkdir(parents=True, exist_ok=True)
    (Path("/workspace/configs/emergency_policies.yaml")).write_text("block_keywords:\n  - shutdown\n")
    k = Kernel(persist_dir=str(tmp_path))
    resp = k.handle("please shutdown now")
    assert resp["status"] == "blocked"
