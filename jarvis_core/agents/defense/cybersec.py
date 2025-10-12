from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List

from ...core.defense_extensions.suricata_ingest import parse_eve_line
from ...core.defense_extensions.soc_correlator import correlate_vision_and_alerts
from ...core.defense_extensions.zeek_ingest import parse_conn_log_line
from ...utils.config import load_yaml
from ...perception.goodseye.vision_for_security import security_detect
from ..base import BaseAgent
from ...defense.risk import score_events
from ...defense.elk_exporter import export_alerts
from ...core.defense_extensions.wazuh_ingest import parse_wazuh_line, store_wazuh

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

        if lower.startswith("correlate vision"):
            # correlate vision event with configured Suricata/Zeek logs
            cfg = load_yaml("/workspace/configs/defense_integrations.yaml")
            suri_path = Path(cfg.get("suricata", {}).get("eve_path", "/var/log/suricata/eve.json"))
            zeek_conn = Path(cfg.get("zeek", {}).get("conn_log_path", "/var/log/zeek/conn.log"))
            alerts: List[Dict[str, Any]] = []
            # Suricata EVE JSON (newline-delimited or continuous JSON array)
            if suri_path.exists():
                try:
                    for ln in suri_path.read_text(errors="ignore").splitlines():
                        try:
                            rec = parse_eve_line(ln)
                            if "error" not in rec:
                                alerts.append(rec)
                        except Exception:
                            continue
                except Exception:
                    pass
            # Zeek conn.log (TSV/space)
            if zeek_conn.exists():
                try:
                    for ln in zeek_conn.read_text(errors="ignore").splitlines():
                        z = parse_conn_log_line(ln)
                        if "error" not in z:
                            # map into alert-like record for correlation timelining
                            alerts.append({
                                "timestamp": z.get("ts"),
                                "event_type": "zeek_conn",
                                "raw": z,
                                "alert": {"severity": 1}
                            })
                except Exception:
                    pass
            vision = security_detect(context.get("image", "frame.jpg"))
            corr = correlate_vision_and_alerts(vision, alerts)
            # Compute a naive risk score
            risk = score_events([{ "severity": e.get("alert", {}).get("severity", "low") } for e in alerts])
            # Optionally export to ELK if configured
            elk_url = context.get("elk_url")
            if elk_url:
                export_alerts(elk_url, context.get("elk_index", "alerts"), alerts)
            return {
                "status": "ok",
                "result": f"correlated={len(corr)} risk={risk:.2f}",
                "artifacts": [{"type": "correlations", "items": corr}],
            }

        if lower.startswith("ingest wazuh "):
            line = task.split(" ", 2)[2]
            rec = parse_wazuh_line(line)
            if "error" in rec:
                return {"status": "error", "result": "invalid wazuh json", "artifacts": []}
            path = store_wazuh(rec)
            return {"status": "ok", "result": "wazuh alert ingested", "artifacts": [{"type": "log", "path": path}]}

        return {"status": "error", "result": "unknown cybersec command", "artifacts": []}
