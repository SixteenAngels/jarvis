from __future__ import annotations

from pathlib import Path

from jarvis_core.agents.research import ResearchAgent


def test_pdf_ingest_graceful_without_dependency(tmp_path: Path) -> None:
    # Create a fake PDF (not a real PDF) to ensure graceful handling
    pdf = tmp_path / "doc.pdf"
    pdf.write_text("This is not a real PDF but should not crash.")

    agent = ResearchAgent()
    res = agent.execute(f"ingest {pdf}", {})
    assert res["status"] == "ok"  # even if no text extracted, it should not crash
