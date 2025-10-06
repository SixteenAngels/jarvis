from __future__ import annotations

import os
from typing import Dict, Any, List

SEC_LOG_DIR = "/workspace/data/logs/security"
os.makedirs(SEC_LOG_DIR, exist_ok=True)


def parse_conn_log_line(line: str) -> Dict[str, Any]:
    # Zeek TSV/space logs: simplistic parser for demo
    parts = line.strip().split()
    if len(parts) < 5:
        return {"error": "invalid_line", "raw": line}
    return {
        "ts": parts[0],
        "uid": parts[1],
        "orig_h": parts[2],
        "resp_h": parts[3],
        "proto": parts[4],
    }
