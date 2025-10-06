from __future__ import annotations

from dataclasses import dataclass
from typing import List


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
    def evaluate(self, user_input: str) -> PolicyDecision:
        text = (user_input or "").lower()
        for k in DANGEROUS_KEYWORDS:
            if k in text:
                return PolicyDecision(False, f"Blocked by policy: contains '{k}'")
        return PolicyDecision(True, "OK")
