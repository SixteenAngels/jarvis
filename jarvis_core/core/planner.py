from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class PlanStep:
    description: str


class Planner:
    def decompose(self, goal: str) -> List[PlanStep]:
        goal_l = (goal or "").lower()
        steps: List[PlanStep] = []
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
