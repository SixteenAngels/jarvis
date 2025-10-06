from __future__ import annotations

from typing import Dict, Any

from ..base import BaseAgent


class EnergyMonitorAgent(BaseAgent):
    name: str = "energy_monitor"
    intents = ["energy", "power", "meter"]

    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "ok", "result": "energy monitor stub", "artifacts": []}
