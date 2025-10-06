from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path
import yaml


@dataclass
class ActionResult:
    status: str
    message: str


class ActionManager:
    def __init__(self, approvals_path: str | None = "/workspace/configs/approvals.yaml") -> None:
        self.approvals = self._load_approvals(approvals_path)

    def _load_approvals(self, path: str | None) -> Dict[str, Any]:
        if path and Path(path).exists():
            try:
                return yaml.safe_load(Path(path).read_text()) or {}
            except Exception:
                return {}
        return {}

    def request(self, action: str, params: Dict[str, Any]) -> ActionResult:
        # Enforce approvals from config
        if action == "notify":
            return ActionResult("ok", f"Notification sent: {params.get('subject', '(no subject)')}")

        rules = self.approvals.get("responses", {})
        rule = rules.get(action, {})
        requires_approval = bool(rule.get("requires_approval", True))
        approved = bool(params.get("approved", False))
        if requires_approval and not approved:
            return ActionResult("requires_approval", f"Action '{action}' requires approval")
        return ActionResult("ok", f"Action '{action}' executed (simulated)")
