from __future__ import annotations

import os
from jarvis_core.core.planner import Planner
from jarvis_core.core.reflection import Reflection
from jarvis_core.core.policy import Policy


def test_planner_llm_outline_runs() -> None:
    p = Planner()
    steps = p.decompose("design a temperature sensor")
    assert steps and len(steps) >= 1


def test_reflection_llm_review_runs() -> None:
    r = Reflection()
    decision = r.assess({"result": "Some short output."})
    assert decision.get("action") in {"accept", "retry"}


def test_policy_config_blocks_custom_keyword(tmp_path) -> None:
    cfg = tmp_path / "policy.yaml"
    cfg.write_text("block_keywords:\n  - foobar\n")
    pol = Policy(config_path=str(cfg))
    out = pol.evaluate("Please run foobar")
    assert out.allowed is False
