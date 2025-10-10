from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path
import yaml
import os
from ..utils.signatures import verify_hmac, verify_rsa
from ..utils.config import load_yaml


@dataclass
class ActionResult:
    status: str
    message: str


class ActionManager:
    def __init__(self, approvals_path: str | None = "/workspace/configs/approvals.yaml") -> None:
        self.approvals = self._load_approvals(approvals_path)
        self.features = load_yaml("/workspace/configs/features.yaml").get("features", {})

    def _load_approvals(self, path: str | None) -> Dict[str, Any]:
        if path and Path(path).exists():
            try:
                return yaml.safe_load(Path(path).read_text()) or {}
            except Exception:
                return {}
        return {}

    def _verify_signed(self, payload: bytes, params: Dict[str, Any]) -> bool:
        if not self.features.get("signed_approvals"):
            return True
        key = os.getenv("SIGNING_KEY")
        sig = params.get("signature")
        if key and isinstance(sig, (bytes, str)):
            try:
                sig_bytes = sig if isinstance(sig, bytes) else bytes.fromhex(sig)
                return verify_hmac(payload, key.encode("utf-8"), sig_bytes)
            except Exception:
                return False
        pub = os.getenv("PUBLIC_KEY")
        if pub and isinstance(sig, (bytes, str)):
            try:
                sig_bytes = sig if isinstance(sig, bytes) else bytes.fromhex(sig)
                return verify_rsa(payload, sig_bytes, pub.encode("utf-8"))
            except Exception:
                return False
        return False

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
        # Optional signature verification
        if self.features.get("signed_approvals"):
            payload = f"{action}:{params}".encode("utf-8")
            if not self._verify_signed(payload, params):
                return ActionResult("denied", "signature verification failed")
        return ActionResult("ok", f"Action '{action}' executed (simulated)")
