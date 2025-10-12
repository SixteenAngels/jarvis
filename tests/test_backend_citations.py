from __future__ import annotations

from pathlib import Path

from jarvis_core.agents.research import ResearchAgent


def test_backend_factory_memory(tmp_path: Path) -> None:
    a = ResearchAgent(backend="memory")
    f = tmp_path / "d.txt"
    f.write_text("backend factory test")
    a.execute(f"ingest {f}", {})
    res = a.execute("query backend", {})
    assert res["status"] == "ok"


def test_citation_snippet(tmp_path: Path) -> None:
    a = ResearchAgent()
    f = tmp_path / "s.txt"
    f.write_text("snippet alpha beta")
    a.execute(f"ingest {f}", {})
    res = a.execute("query alpha", {})
    cites = [x for x in res.get("artifacts", []) if x.get("type") == "citations"][0]
    assert cites["items"][0].get("snippet")
