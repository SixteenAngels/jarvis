from __future__ import annotations

from pathlib import Path

from jarvis_core.core.router import Router
from jarvis_core.agents.robotics import RoboticsAgent, ROBOT_LOG
from jarvis_core.agents.civil import CivilAgent


def test_robotics_logs_action(tmp_path: Path) -> None:
    # Ensure log file is clean per test
    if ROBOT_LOG.exists():
        ROBOT_LOG.unlink()
    r = Router(agents=[RoboticsAgent()])
    res = r.route("robot move x=1 y=2 z=3")
    assert res["status"] == "ok"
    assert ROBOT_LOG.exists()
    content = ROBOT_LOG.read_text()
    assert "move" in content and "x" in content


def test_civil_safety_factor() -> None:
    r = Router(agents=[CivilAgent()])
    res = r.route("safety factor strength=300000000 stress=150000000")
    assert res["status"] == "ok"
    assert "SF" in res["result"]
