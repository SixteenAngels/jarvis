from __future__ import annotations

from typing import Dict, Any

from ..base import BaseAgent
from ...execution.action_manager import ActionManager


class EmergencyAgent(BaseAgent):
    name: str = "emergency"
    intents = ["emergency", "lockdown", "alarm"]

    def __init__(self) -> None:
        super().__init__()
        self.am = ActionManager()

    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Example: lockdown requires approval
        resp = self.am.request("isolate_host", context)
        return {"status": resp.status, "result": resp.message, "artifacts": []}
