from __future__ import annotations

from jarvis_core.core.router import Router
from jarvis_core.agents.biomedical import BiomedicalAgent
from jarvis_core.agents.electrical import ElectricalAgent


def test_biomedical_advisory_contains_disclaimer() -> None:
    router = Router(agents=[BiomedicalAgent()])
    res = router.route("medical: user reports fever and cough")
    assert res["status"] == "ok"
    assert "advisory only" in res["result"].lower()


def test_electrical_led_resistor_calc() -> None:
    router = Router(agents=[ElectricalAgent()])
    res = router.route("led resistor Vs=5 Vf=2 I=10")
    assert res["status"] == "ok"
    assert "Ω" in res["result"]


def test_router_default_includes_biomedical_and_electrical() -> None:
    router = Router()
    # Should be able to handle both without specifying agents
    r1 = router.route("medical: headache")
    r2 = router.route("ohm V=5 I=0.01")
    assert r1["status"] == "ok"
    assert r2["status"] == "ok" and "Ω" in r2["result"]
