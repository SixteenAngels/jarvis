from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Any, List


def correlate_vision_and_alerts(vision_event: Dict[str, Any], alerts: List[Dict[str, Any]], window_seconds: int = 30) -> List[Dict[str, Any]]:
    """Basic time-window correlation between a vision event and Suricata-like alerts.

    Returns list of correlated entries with both vision and alert data.
    """
    correlated: List[Dict[str, Any]] = []
    vt = datetime.utcfromtimestamp(float(vision_event.get("timestamp", 0)))
    window = timedelta(seconds=window_seconds)
    for a in alerts:
        ts = a.get("timestamp")
        try:
            at = datetime.fromisoformat(ts)
        except Exception:
            continue
        if abs((vt - at).total_seconds()) <= window.total_seconds():
            sev = 0
            try:
                sev = int(a.get("alert", {}).get("severity", 0))
            except Exception:
                sev = 0
            if sev >= 2:
                correlated.append({"vision": vision_event, "alert": a})
    return correlated
