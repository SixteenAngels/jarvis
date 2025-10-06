from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, Any

SEC_LOG_DIR = "/workspace/data/logs/security"
os.makedirs(SEC_LOG_DIR, exist_ok=True)


def parse_eve_line(line: str) -> Dict[str, Any]:
    """Parse a single Suricata EVE JSON line (defensive ingest)."""
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return {"error": "invalid_json", "raw": line}
    # Basic normalization
    rec = {
        "timestamp": data.get("timestamp"),
        "event_type": data.get("event_type"),
        "src_ip": data.get("src_ip"),
        "dest_ip": data.get("dest_ip"),
        "alert": data.get("alert", {}),
        "flow": data.get("flow", {}),
        "raw": data,
    }
    return rec


def store_alert(parsed: Dict[str, Any]) -> str:
    """Append parsed alert to daily security log (immutable append)."""
    dt = datetime.utcnow().strftime("%Y-%m-%d")
    path = os.path.join(SEC_LOG_DIR, f"suricata_{dt}.ndjson")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(parsed) + "\n")
    return path
