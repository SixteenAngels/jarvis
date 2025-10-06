from __future__ import annotations

from pathlib import Path

from jarvis_core.core.router import Router
from jarvis_core.agents.defense_agent import DefenseAgent


def test_defense_scan_detects_patterns(tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    log.write_text("User admin failed password from 10.0.0.1\nPossible UNION SELECT attack detected\n")

    r = Router(agents=[DefenseAgent()])
    res = r.route(f"scan logs {log}")
    assert res["status"] == "ok"
    assert "auth_failed" in res["result"] or "sql_injection" in res["result"]


def test_defense_analyze_event_inline() -> None:
    r = Router(agents=[DefenseAgent()])
    res = r.route("analyze event: blocked 192.168.1.10 due to unauthorized access")
    assert res["status"] == "ok"
    assert "unauthorized" in res["result"] or "suspicious_ip" in res["result"]
