from __future__ import annotations

from typing import Dict, Any, List

from .base import BaseAgent
from ..execution.sandbox import Sandbox


class SystemAgent(BaseAgent):
    name: str = "system"
    intents: List[str] = [
        "system",
        "run",
        "command",
        "shell",
        "list files",
        "uname",
        "python",
    ]

    def __init__(self, sandbox: Sandbox | None = None) -> None:
        super().__init__()
        self.sandbox = sandbox or Sandbox()

    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Expect commands like: "run: echo hello" or "run echo hello"
        lower = task.strip()
        cmd = None
        if lower.lower().startswith("run:"):
            cmd = lower.split(":", 1)[1].strip()
        elif lower.lower().startswith("run "):
            cmd = lower.split(" ", 1)[1].strip()
        elif lower.lower().startswith("system "):
            cmd = lower.split(" ", 1)[1].strip()

        if not cmd:
            # best-effort: treat entire task as command
            cmd = lower

        result = self.sandbox.run(cmd, timeout=int(context.get("timeout", 10)))
        return {
            "status": result.status,
            "result": result.stdout if result.stdout else result.stderr,
            "artifacts": [
                {"type": "exec", "returncode": result.returncode}
            ],
        }
