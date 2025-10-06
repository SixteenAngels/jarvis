from __future__ import annotations

from typing import Dict, Any

from ..base import BaseAgent


class HomeAssistantAgent(BaseAgent):
    name: str = "home_assistant"
    intents = ["home assistant", "mqtt", "light", "device"]

    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "ok", "result": "home assistant stub", "artifacts": []}
