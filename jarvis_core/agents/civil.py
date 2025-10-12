from __future__ import annotations

from typing import Dict, Any, List

from .base import BaseAgent


class CivilAgent(BaseAgent):
    name: str = "civil"
    intents: List[str] = [
        "civil",
        "structural",
        "beam",
        "load",
        "safety factor",
        "foundation",
    ]

    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        lower = task.lower().strip()
        if lower.startswith("safety factor"):
            # format: safety factor strength=<Pa> stress=<Pa>
            params = self._parse_params(lower.replace("safety factor", "").strip())
            strength = float(params.get("strength", 250e6))
            stress = float(params.get("stress", 100e6))
            sf = strength / max(stress, 1e-9)
            return {"status": "ok", "result": f"SF ≈ {sf:.2f}", "artifacts": []}
        return {"status": "error", "result": "Unknown civil command", "artifacts": []}

    def _parse_params(self, s: str) -> Dict[str, float]:
        params: Dict[str, float] = {}
        for part in s.split():
            if "=" in part:
                k, v = part.split("=", 1)
                try:
                    params[k.strip()] = float(v)
                except Exception:
                    pass
        return params
