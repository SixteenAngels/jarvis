from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Tuple

from .base import BaseAgent

ALERTS_DIR = Path("/workspace/data/logs")
ALERTS_DIR.mkdir(parents=True, exist_ok=True)
ALERTS_PATH = ALERTS_DIR / "alerts.jsonl"


@dataclass
class DetectionRule:
    name: str
    pattern: re.Pattern[str]
    severity: str  # info | low | medium | high | critical


def _default_rules() -> List[DetectionRule]:
    return [
        DetectionRule("auth_failed", re.compile(r"failed password|authentication failure", re.I), "medium"),
        DetectionRule("unauthorized_access", re.compile(r"unauthorized|forbidden", re.I), "medium"),
        DetectionRule("sql_injection", re.compile(r"union\s+select|drop\s+table|xp_cmdshell", re.I), "high"),
        DetectionRule("xss", re.compile(r"<script>|onerror=|javascript:\s*", re.I), "high"),
        DetectionRule("rfi_lfi", re.compile(r"\.\./|/etc/passwd|http://.*\?", re.I), "high"),
        DetectionRule("suspicious_ip", re.compile(r"(\d{1,3}\.){3}\d{1,3}.*(blocked|denied)", re.I), "low"),
    ]


class DefenseAgent(BaseAgent):
    name: str = "defense"
    intents: List[str] = [
        "defense",
        "security",
        "scan",
        "ids",
        "alert",
        "log",
    ]

    def __init__(self, rules: List[DetectionRule] | None = None) -> None:
        super().__init__()
        self.rules = rules or _default_rules()

    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        lower = task.strip().lower()
        if lower.startswith("scan logs "):
            path = task.split(" ", 2)[2]
            result = self._scan_logs(Path(path))
            self._persist_alerts(result["events"])  # write individual events
            return {
                "status": "ok",
                "result": self._format_summary(result),
                "artifacts": [{"type": "alerts", "path": str(ALERTS_PATH)}],
            }
        if lower.startswith("analyze event:"):
            text = task.split(":", 1)[1]
            evs = self._detect_in_text(text)
            self._persist_alerts(evs)
            return {
                "status": "ok" if evs else "ok",
                "result": self._format_summary({"counts": self._counts(evs), "events": evs}),
                "artifacts": [{"type": "alerts", "path": str(ALERTS_PATH)}],
            }
        return {"status": "error", "result": "Unknown defense command", "artifacts": []}

    # ---------------- internal ----------------
    def _scan_logs(self, path: Path) -> Dict[str, Any]:
        events: List[Dict[str, Any]] = []
        if path.is_dir():
            files = [p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in {".log", ".txt"}]
        else:
            files = [path]
        for fp in files:
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            events.extend(self._detect_in_text(text, source=str(fp)))
        counts = self._counts(events)
        return {"counts": counts, "events": events}

    def _detect_in_text(self, text: str, source: str | None = None) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        for rule in self.rules:
            for m in rule.pattern.finditer(text):
                snippet = text[max(0, m.start()-40): m.end()+40]
                events.append({
                    "rule": rule.name,
                    "severity": rule.severity,
                    "source": source or "inline",
                    "snippet": snippet.strip().replace("\n", " "),
                    "recommendation": self._recommend(rule.severity),
                })
        return events

    def _counts(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for ev in events:
            key = f"{ev['rule']}:{ev['severity']}"
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _persist_alerts(self, events: List[Dict[str, Any]]) -> None:
        if not events:
            return
        with ALERTS_PATH.open("a", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev) + "\n")

    def _recommend(self, severity: str) -> str:
        base = "Apply defense-in-depth: isolate affected systems, patch, rotate credentials, increase logging."
        if severity in {"high", "critical"}:
            return base + " Consider incident response playbook and forensics."
        return base

    def _format_summary(self, result: Dict[str, Any]) -> str:
        counts = result.get("counts", {})
        if not counts:
            return "No suspicious events detected."
        parts = [f"{k}={v}" for k, v in sorted(counts.items())]
        return "; ".join(parts)
