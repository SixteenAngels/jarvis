from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List

from ...core.defense_extensions.suricata_ingest import parse_eve_line
from ...core.defense_extensions.soc_correlator import correlate_vision_and_alerts
from ...perception.goodseye.vision_for_security import security_detect
from ..base import BaseAgent

SEC_DIR = Path("/workspace/data/logs/security")
SEC_DIR.mkdir(parents=True, exist_ok=True)


class CybersecDefenseAgent(BaseAgent):
    name: str = "cybersec_defense"
    intents: List[str] = [
        "suricata",
        "zeek",
        "correlate",
        "vision",
        "security",
        "defense",
    ]

    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        lower = task.strip().lower()
        if lower.startswith("ingest suricata "):
            # ingest suricata eve.json line
            line = task.split(" ", 2)[2]
            rec = parse_eve_line(line)
            if "error" in rec:
                return {"status": "error", "result": "invalid suricata json", "artifacts": []}
            # append to file for demo
            out = SEC_DIR / "suricata_manual.ndjson"
            with out.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
            return {"status": "ok", "result": "suricata alert ingested", "artifacts": [{"type": "log", "path": str(out)}]}

        if lower.startswith("correlate vision "):
            # correlate vision event with alerts from a file path
            path_str = task.split(" ", 2)[2]
            alerts_path = Path(path_str)
            if not alerts_path.exists():
                return {"status": "error", "result": "alerts file not found", "artifacts": []}
            alerts: List[Dict[str, Any]] = []
            for line in alerts_path.read_text().splitlines():
                try:
                    alerts.append(json.loads(line))
                except Exception:
                    continue
            vision = security_detect(context.get("image", "frame.jpg"))
            corr = correlate_vision_and_alerts(vision, alerts)
            return {
                "status": "ok",
                "result": f"correlated={len(corr)}",
                "artifacts": [{"type": "correlations", "items": corr}],
            }

        return {"status": "error", "result": "unknown cybersec command", "artifacts": []}
