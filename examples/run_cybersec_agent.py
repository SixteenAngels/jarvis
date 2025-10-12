"""
Example: Cybersec agent ingest and correlation demo.

Usage:
  python examples/run_cybersec_agent.py /path/to/alerts.ndjson
"""
from __future__ import annotations

import sys
from jarvis_core.core.router import Router
from jarvis_core.agents.defense.cybersec import CybersecDefenseAgent


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "/workspace/data/logs/security/suricata_manual.ndjson"
    r = Router(agents=[CybersecDefenseAgent()])
    # correlate
    print(r.route(f"correlate vision {path}", {"image": "frame.jpg"}))


if __name__ == "__main__":
    main()
