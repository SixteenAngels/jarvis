from __future__ import annotations

"""Wazuh ingest (defensive only).

Parses Wazuh JSON lines and normalizes a minimal subset of fields for storage
under /workspace/data/logs/security.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any

SEC_LOG_DIR = "/workspace/data/logs/security"
os.makedirs(SEC_LOG_DIR, exist_ok=True)


def parse_wazuh_line(line: str) -> Dict[str, Any]:
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return {"error": "invalid_json", "raw": line}
    # Normalize minimal fields
    alert = data.get("rule", {})
    sev = alert.get("level", 0)
    # Map level to severity bands
    if sev >= 12:
        severity = "critical"
    elif sev >= 8:
        severity = "high"
    elif sev >= 4:
        severity = "medium"
    else:
        severity = "low"
    rec = {
        "timestamp": data.get("timestamp") or data.get("@timestamp"),
        "agent": data.get("agent", {}).get("name"),
        "rule": alert,
        "severity": severity,
        "raw": data,
    }
    return rec


def store_wazuh(parsed: Dict[str, Any]) -> str:
    dt = datetime.utcnow().strftime("%Y-%m-%d")
    path = os.path.join(SEC_LOG_DIR, f"wazuh_{dt}.ndjson")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(parsed) + "\n")
    return path
