from __future__ import annotations

from pathlib import Path

from jarvis_core.core.router import Router
from jarvis_core.agents.mechanical import MechanicalAgent
from jarvis_core.agents.software import SoftwareAgent


def test_mechanical_beam_deflection() -> None:
    r = Router(agents=[MechanicalAgent()])
    res = r.route("beam deflection F=100 L=1 E=200000000000 I=1e-6")
    assert res["status"] == "ok"
    assert "δ" in res["result"]


def test_mechanical_gear_ratio() -> None:
    r = Router(agents=[MechanicalAgent()])
    res = r.route("gear ratio driver=20 driven=60")
    assert res["status"] == "ok"
    assert "ratio" in res["result"].lower()


def test_software_scaffold_cli(tmp_path: Path) -> None:
    r = Router(agents=[SoftwareAgent()])
    res = r.route("scaffold cli demo")
    assert res["status"] == "ok"
    assert "demo_cli" in res["result"]
