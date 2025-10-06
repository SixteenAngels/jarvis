from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List

from .base import BaseAgent

ROBOT_LOG = Path("/workspace/data/logs/robot_actions.jsonl")
ROBOT_LOG.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class RobotCommand:
    device: str
    action: str
    params: Dict[str, Any]

    def to_json(self) -> str:
        return json.dumps({"device": self.device, "action": self.action, "params": self.params})


class RoboticsAgent(BaseAgent):
    name: str = "robotics"
    intents: List[str] = [
        "robot",
        "drone",
        "arm",
        "move",
        "navigate",
        "pick",
        "place",
    ]

    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Example formats: "robot move x=1 y=2 z=3", "drone navigate lat=.. lon=.. alt=.."
        lower = task.strip().lower()
        if lower.startswith("robot ") or lower.startswith("drone ") or lower.startswith("arm "):
            device, rest = task.split(" ", 1)
            if " " in rest:
                action, argstr = rest.split(" ", 1)
            else:
                action, argstr = rest, ""
            params = self._parse_params(argstr)
            cmd = RobotCommand(device=device, action=action, params=params)
            self._log(cmd)
            return {"status": "ok", "result": f"{device} -> {action} {params}", "artifacts": [{"type": "robot_log", "path": str(ROBOT_LOG)}]}
        return {"status": "error", "result": "Unknown robotics command", "artifacts": []}

    def _parse_params(self, s: str) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        for part in s.split():
            if "=" in part:
                k, v = part.split("=", 1)
                try:
                    if v.replace('.', '', 1).isdigit():
                        params[k] = float(v)
                    else:
                        params[k] = v
                except Exception:
                    params[k] = v
        return params

    def _log(self, cmd: RobotCommand) -> None:
        with ROBOT_LOG.open("a", encoding="utf-8") as f:
            f.write(cmd.to_json() + "\n")
