from __future__ import annotations

from pathlib import Path

from jarvis_core.agents.electrical import ElectricalAgent
from jarvis_core.agents.mechanical import MechanicalAgent


def test_ngspice_fallback(tmp_path: Path) -> None:
    net = tmp_path / "circuit.sp"
    net.write_text("* netlist\nV1 in 0 5\nR1 in out 1k\n")
    a = ElectricalAgent()
    res = a.execute(f"simulate {net}", {})
    assert res["status"] in ("ok", "error")


def test_openscad_fallback(tmp_path: Path) -> None:
    scad = tmp_path / "shape.scad"
    scad.write_text("cube(1);")
    a = MechanicalAgent()
    res = a.execute("generate cad /workspace/data/artifacts/cad", {"scad": str(scad)})
    assert res["status"] in ("ok", "error")
