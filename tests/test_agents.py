from __future__ import annotations

from pathlib import Path

from jarvis_core.agents.research import ResearchAgent
from jarvis_core.core.router import Router


def test_research_ingest_and_query(tmp_path: Path) -> None:
    # Create a small corpus
    doc = tmp_path / "doc.txt"
    doc.write_text("Python is a programming language. It is popular for AI research.")

    agent = ResearchAgent()
    # Ingest file
    res = agent.execute(f"ingest {doc}", {})
    assert res["status"] == "ok"

    # Query
    q = agent.execute("query What is Python used for?", {"k": 3})
    assert q["status"] == "ok"
    assert "Python" in q["result"] or "programming" in q["result"]


def test_router_routes_to_research_agent(tmp_path: Path) -> None:
    doc = tmp_path / "doc.txt"
    doc.write_text("FAISS-like index allows vector search over embeddings.")

    router = Router(agents=[ResearchAgent()])
    # route ingest to ResearchAgent
    r1 = router.route(f"ingest {doc}")
    assert r1["status"] == "ok"

    r2 = router.route("query vector search embeddings", {"k": 2})
    assert r2["status"] == "ok" and len(r2["result"]) > 0
