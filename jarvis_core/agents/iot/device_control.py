from __future__ import annotations

from typing import Dict, Any

from ..base import BaseAgent


class DeviceControlAgent(BaseAgent):
    name: str = "device_control"
    intents = ["device control", "switch", "toggle"]

    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "ok", "result": "device control stub", "artifacts": []}
