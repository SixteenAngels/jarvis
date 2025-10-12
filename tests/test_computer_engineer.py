from __future__ import annotations

from pathlib import Path

from jarvis_core.core.router import Router
from jarvis_core.agents.engineering.software import ComputerEngineerAgent


def test_computer_engineer_analyze(tmp_path: Path) -> None:
    f = tmp_path / "a.py"
    f.write_text("print('x')\n")
    r = Router(agents=[ComputerEngineerAgent()])
    res = r.route(f"analyze code {tmp_path}")
    assert res["status"] == "ok"
    assert "Analyzed" in res["result"]


def test_computer_engineer_scaffold(tmp_path: Path) -> None:
    r = Router(agents=[ComputerEngineerAgent()])
    res = r.route("scaffold project democe")
    assert res["status"] == "ok" and "scaffolded" in res["result"]
