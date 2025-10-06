from __future__ import annotations

from typing import Dict, Any

from ..agents.base import BaseAgent


class DeviceControlAgent(BaseAgent):
    name: str = "device_control"

    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "ok", "result": "device control stub", "artifacts": []}
