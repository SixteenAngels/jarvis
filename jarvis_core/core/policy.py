from __future__ import annotations

from dataclasses import dataclass
from typing import List
from pathlib import Path
import yaml


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str


DANGEROUS_KEYWORDS: List[str] = [
    "rm -rf",
    "mkfs",
    "format disk",
    "exploit",
    "payload",
    "ransomware",
    "dd if=/dev/",
]


class Policy:
    def __init__(self, config_path: str | None = "/workspace/configs/policy.yaml", emergency_path: str | None = "/workspace/configs/emergency_policies.yaml") -> None:
        self.keywords: List[str] = list(DANGEROUS_KEYWORDS)
        if config_path and Path(config_path).exists():
            try:
                data = yaml.safe_load(Path(config_path).read_text()) or {}
                self.keywords = list(set(self.keywords + list(data.get("block_keywords", []))))
            except Exception:
                pass
        # Emergency mode: add stricter keywords
        if emergency_path and Path(emergency_path).exists():
            try:
                data = yaml.safe_load(Path(emergency_path).read_text()) or {}
                self.keywords = list(set(self.keywords + list(data.get("block_keywords", []))))
            except Exception:
                pass

    def evaluate(self, user_input: str) -> PolicyDecision:
        text = (user_input or "").lower()
        for k in self.keywords:
            if k and k.lower() in text:
                return PolicyDecision(False, f"Blocked by policy: contains '{k}'")
        return PolicyDecision(True, "OK")
