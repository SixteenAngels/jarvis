from __future__ import annotations

import json
import requests
from typing import Dict, Any, List


def export_alerts(elk_url: str, index: str, events: List[Dict[str, Any]]) -> bool:
    """Send alerts to ELK/Elasticsearch (simplified bulk index)."""
    try:
        bulk = []
        for ev in events:
            bulk.append(json.dumps({"index": {"_index": index}}))
            bulk.append(json.dumps(ev))
        data = "\n".join(bulk) + "\n"
        resp = requests.post(f"{elk_url}/_bulk", data=data, headers={"Content-Type": "application/x-ndjson"}, timeout=5)
        return resp.status_code < 300
    except Exception:
        return False
