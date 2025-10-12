from __future__ import annotations

from jarvis_core.core.vectorstore.faiss_index import InMemoryVectorIndex
from jarvis_core.core.vectorstore.embedding import EmbeddingAdapter
from jarvis_core.agents.research import ResearchAgent


def test_embedding_adapter_fallback_runs():
    adapter = EmbeddingAdapter()
    vecs = adapter.encode(["hello world", "another doc"])
    assert len(vecs) == 2 and all(isinstance(v, list) for v in vecs)


def test_research_agent_returns_citations(tmp_path):
    # Use in-memory index for speed
    idx = InMemoryVectorIndex()
    agent = ResearchAgent(index=idx)
    doc = tmp_path / "note.txt"
    doc.write_text("Citations should include the source path.")
    agent.execute(f"ingest {doc}", {})
    res = agent.execute("query citations", {"k": 2})
    assert res["status"] == "ok"
    artifacts = res.get("artifacts", [])
    cites = [a for a in artifacts if a.get("type") == "citations"]
    assert cites and len(cites[0].get("items", [])) >= 1
