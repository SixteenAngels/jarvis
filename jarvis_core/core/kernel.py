from __future__ import annotations

from typing import Dict, Any, List

from .policy import Policy
from .planner import Planner, PlanStep
from .reflection import Reflection
from .router import Router
from .memory.short_term import ShortTermMemory
from .memory.long_term import LongTermMemory


class Kernel:
    def __init__(self, persist_dir: str = "/workspace/data/vectorstore") -> None:
        self.policy = Policy()
        self.planner = Planner()
        self.reflection = Reflection()
        self.router = Router()
        self.short_mem = ShortTermMemory()
        self.long_mem = LongTermMemory(persist_dir)

    def handle(self, user_input: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        context = context or {}
        decision = self.policy.evaluate(user_input)
        if not decision.allowed:
            return {"status": "blocked", "result": decision.reason, "artifacts": []}

        self.short_mem.add(user_input)
        steps: List[PlanStep] = self.planner.decompose(user_input)
        last_resp: Dict[str, Any] = {"status": "ok", "result": "", "artifacts": []}
        for step in steps:
            resp = self.router.route(step.description, context)
            assess = self.reflection.assess(resp)
            if assess.get("action") == "retry":
                # simple retry with modified params
                resp = self.router.route(step.description, {**context, **assess.get("params", {})})
            last_resp = resp
            # Persist meaningful outputs to long-term memory
            if resp.get("result"):
                self.long_mem.add_document(str(resp.get("result")), source="kernel")
        self.long_mem.save()
        return last_resp
