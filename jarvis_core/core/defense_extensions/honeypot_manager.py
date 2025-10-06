from __future__ import annotations

from typing import Dict, Any

# Placeholder for Cowrie honeypot manager.


def start_honeypot(instance_name: str) -> Dict[str, Any]:
    return {"status": "started", "instance": instance_name}


def stop_honeypot(instance_name: str) -> Dict[str, Any]:
    return {"status": "stopped", "instance": instance_name}
