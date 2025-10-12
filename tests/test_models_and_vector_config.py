from __future__ import annotations

from pathlib import Path

from jarvis_core.models.selector import ModelSelector
from jarvis_core.agents.research import ResearchAgent


def test_model_selector_prefers_local_when_configured(tmp_path: Path, monkeypatch) -> None:
    cfg = tmp_path / "models.yaml"
    cfg.write_text("selector:\n  prefer: local\n  backoff_seconds: 0\n")
    monkeypatch.setenv("MODELS_CFG", str(cfg))
    # Selector loads default path; we pass override config directly for test
    ms = ModelSelector(config={"prefer": "local", "backoff_seconds": 0})
    out = ms.generate("hello")
    assert out.startswith("[local-llm]")


def test_research_agent_reads_vector_backend(tmp_path: Path) -> None:
    # Write vectorstore config
    (Path("/workspace/configs")).mkdir(parents=True, exist_ok=True)
    (Path("/workspace/configs/vectorstore.yaml")).write_text("backend: memory\n")
    a = ResearchAgent(persist_dir=str(tmp_path))
    f = tmp_path / "x.txt"
    f.write_text("config read ok")
    res = a.execute(f"ingest {f}", {})
    assert res["status"] == "ok"
