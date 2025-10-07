from __future__ import annotations
"""Jarvis Core Kernel

This module defines the central orchestrator (Kernel) for Jarvis Core. The
Kernel coordinates the high-level flow for every user command:

    Policy → Planner → Router/Agents → Reflection → Memory

Key components used:
- Policy: Blocks unsafe requests via configurable keywords and emergency rules
- Planner: Decomposes a goal into one or more PlanStep items
- Router: Selects an agent for each step and executes it
- Reflection: Assesses results and can trigger a retry with modified params
- Memory: Short-term buffer for session state and long-term vector memory

The Kernel exposes a single handle() method consumed by CLI/HTTP APIs.
"""

from typing import Dict, Any, List

from .policy import Policy
from .planner import Planner, PlanStep
from .reflection import Reflection
from .router import Router
from .memory.short_term import ShortTermMemory
from .memory.long_term import LongTermMemory
from ..utils.logging import get_logger


class Kernel:
    """Central orchestrator for Jarvis Core.

    The Kernel enforces the safety-first execution model and coordinates
    task planning, routing to agents, reflection, and memory persistence.

    Args:
        persist_dir: Filesystem directory for long-term vector memory.
    """

    def __init__(self, persist_dir: str = "/workspace/data/vectorstore") -> None:
        self.logger = get_logger()
        self.policy = Policy()
        self.planner = Planner()
        self.reflection = Reflection()
        self.router = Router()
        self.short_mem = ShortTermMemory()
        self.long_mem = LongTermMemory(persist_dir)

    def handle(self, user_input: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Handle a single user request end-to-end.

        The method evaluates policy, plans steps, routes to agents, performs
        a reflection pass, and persists results to long-term memory.

        Args:
            user_input: Natural language goal or command.
            context: Optional execution context (e.g., query params like k).

        Returns:
            A structured response dict with keys: status, result, artifacts.

        Side effects:
            - Appends user input to short-term memory
            - Writes agent results to long-term memory
            - Emits audit logs via the central logger
        """
        context = context or {}
        self.logger.info(f"handle: {user_input}")
        decision = self.policy.evaluate(user_input)
        if not decision.allowed:
            self.logger.warning(f"blocked by policy: {decision.reason}")
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
            self.logger.info(f"step: {step.description} -> {resp.get('status')}")
        self.long_mem.save()
        self.logger.info("completed request")
        return last_resp
