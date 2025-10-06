from __future__ import annotations

from typing import Dict, Any


class Reflection:
    def assess(self, result: Dict[str, Any]) -> Dict[str, Any]:
        # Simple heuristic: if empty result, suggest retry with higher k
        text = (result.get("result") or "").strip()
        if not text:
            return {"action": "retry", "params": {"k": 8}}
        return {"action": "accept"}
