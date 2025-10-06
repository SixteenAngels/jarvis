from __future__ import annotations

from typing import Dict, Any
from ..models.selector import ModelSelector


class Reflection:
    def __init__(self) -> None:
        self.models = ModelSelector()

    def assess(self, result: Dict[str, Any]) -> Dict[str, Any]:
        # Simple heuristic: if empty result, suggest retry with higher k
        text = (result.get("result") or "").strip()
        if not text:
            return {"action": "retry", "params": {"k": 8}}
        # Ask model to check quality (placeholder)
        review = self.models.generate(f"Review output quality briefly: {text[:200]}")
        if "improve" in review.lower():
            return {"action": "retry", "params": {"k": 8}}
        return {"action": "accept"}
