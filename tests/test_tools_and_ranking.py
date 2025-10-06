from __future__ import annotations

from pathlib import Path

from jarvis_core.agents.electrical import ElectricalAgent
from jarvis_core.agents.mechanical import MechanicalAgent
from jarvis_core.agents.research import ResearchAgent


def test_spice_simulation_stub(tmp_path: Path) -> None:
    net = tmp_path / "circuit.spice"
    net.write_text("* netlist\nV1 in 0 5\nR1 in out 1k\n")
    a = ElectricalAgent()
    res = a.execute(f"simulate {net}", {})
    assert res["status"] == "ok"


def test_generate_cad_stub(tmp_path: Path) -> None:
    a = MechanicalAgent()
    res = a.execute(f"generate cad {tmp_path}", {})
    assert res["status"] == "ok"
    p = Path(res["artifacts"][0]["path"]).resolve()
    assert p.exists()


def test_bm25_boosts_ranking(tmp_path: Path) -> None:
    r = ResearchAgent()
    a = tmp_path / "a.txt"; b = tmp_path / "b.txt"
    a.write_text("apple banana cherry\n"*10)
    b.write_text("delta echo foxtrot\n"*10)
    r.execute(f"ingest {tmp_path}", {})
    res = r.execute("query apple", {"k": 2})
    assert res["status"] == "ok"
