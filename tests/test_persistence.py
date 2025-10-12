from __future__ import annotations

from pathlib import Path

from jarvis_core.core.vectorstore.persistent_index import PersistentVectorIndex
from jarvis_core.agents.research import ResearchAgent


def test_persistent_index_save_and_load(tmp_path: Path) -> None:
    idx = PersistentVectorIndex()
    idx.add_texts(["alpha beta", "gamma delta"], [{"source": "a"}, {"source": "b"}])

    idx.save(tmp_path)
    reloaded = PersistentVectorIndex.load(tmp_path)
    assert len(reloaded) == 2
    # search should return something sensible
    res = reloaded.search("alpha", k=1)
    assert res and "alpha" in res[0][2].text


def test_research_agent_uses_persistent_dir(tmp_path: Path) -> None:
    # First instance ingests
    a1 = ResearchAgent(persist_dir=str(tmp_path))
    doc = tmp_path / "note.txt"
    doc.write_text("RAG persistence enables reuse of embeddings across runs.")
    r1 = a1.execute(f"ingest {doc}", {})
    assert r1["status"] == "ok"

    # Second instance loads from disk and can query
    a2 = ResearchAgent(persist_dir=str(tmp_path))
    r2 = a2.execute("query reuse embeddings", {"k": 3})
    assert r2["status"] == "ok" and "RAG" in r2["result"] or "embeddings" in r2["result"]
