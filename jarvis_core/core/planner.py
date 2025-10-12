from __future__ import annotations

from dataclasses import dataclass
from typing import List
from ..models.selector import ModelSelector


@dataclass
class PlanStep:
    description: str


class Planner:
    def __init__(self) -> None:
        self.models = ModelSelector()

    def decompose(self, goal: str) -> List[PlanStep]:
        goal_l = (goal or "").lower()
        steps: List[PlanStep] = []
        # Try LLM outline first
        try:
            outline = self.models.generate(f"Decompose the goal into 2-4 concise steps: {goal}")
            # naive parse: split by ';' or '.'
            parts = [p.strip() for p in outline.split('.') if p.strip()] or [p.strip() for p in outline.split(';') if p.strip()]
            for p in parts[:4]:
                steps.append(PlanStep(description=p))
        except Exception:
            pass
        # Fallback rules
        if not steps:
            # naive decomposition rules
            if goal_l.startswith("ingest"):
                steps.append(PlanStep(description=goal))
                steps.append(PlanStep(description=f"query summary of {goal}"))
            elif any(k in goal_l for k in ["design", "build", "generate"]):
                steps.append(PlanStep(description=f"research: {goal}"))
                steps.append(PlanStep(description=f"execute: {goal}"))
            else:
                steps.append(PlanStep(description=goal))
        return steps
