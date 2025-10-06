from __future__ import annotations

from pathlib import Path

from jarvis_core.agents.research import ResearchAgent


def test_citations_dedup_and_rerank(tmp_path: Path) -> None:
    a = ResearchAgent()
    # two files with overlapping text
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("alpha beta gamma delta epsilon " * 50)
    f2.write_text("alpha beta zeta eta theta " * 50)
    a.execute(f"ingest {tmp_path}", {})
    res = a.execute("query alpha beta", {"k": 5})
    assert res["status"] == "ok"
    cites = [x for x in res.get("artifacts", []) if x.get("type") == "citations"][0]
    items = cites.get("items", [])
    # ensure deduped by source
    sources = [i["source"] for i in items]
    assert len(sources) == len(set(sources))
