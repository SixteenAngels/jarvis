from __future__ import annotations

from typing import Dict, Any, List

SEVERITY_SCORES = {
    "low": 0.1,
    "medium": 0.4,
    "high": 0.7,
    "critical": 1.0,
}


def score_events(events: List[Dict[str, Any]]) -> float:
    score = 0.0
    for ev in events:
        sev = str(ev.get("severity", "low")).lower()
        score += SEVERITY_SCORES.get(sev, 0.1)
    return score
