from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List

from .base import BaseAgent


NOTIFY_DIR = Path("/workspace/data/notifications")
NOTIFY_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Notification:
    channel: str
    subject: str
    body: str

    def serialize(self) -> str:
        return f"[{self.channel}] {self.subject}\n{self.body}\n"


class CommsAgent(BaseAgent):
    name: str = "comms"
    intents: List[str] = [
        "notify",
        "email",
        "message",
        "alert",
        "approval",
    ]

    def __init__(self) -> None:
        super().__init__()

    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        lower = task.strip()
        if lower.lower().startswith("notify "):
            # format: notify <channel>: <subject> | <body>
            payload = lower.split(" ", 1)[1]
            channel, subject, body = self._parse_notify_payload(payload)
            note = Notification(channel=channel, subject=subject, body=body)
            path = self._persist_notification(note)
            return {"status": "ok", "result": f"notified:{channel} -> {subject}", "artifacts": [{"type": "notification", "path": str(path)}]}

        if lower.lower().startswith("email "):
            # format: email to:<addr> subject:<subject> | <body>
            payload = lower.split(" ", 1)[1]
            subject, body = self._parse_email_payload(payload)
            note = Notification(channel="email", subject=subject, body=body)
            path = self._persist_notification(note)
            return {"status": "ok", "result": f"email queued -> {subject}", "artifacts": [{"type": "email", "path": str(path)}]}

        return {"status": "error", "result": "Unknown comms command", "artifacts": []}

    def _parse_notify_payload(self, payload: str) -> tuple[str, str, str]:
        # expected: "<channel>: <subject> | <body>"
        if ":" not in payload or "|" not in payload:
            return ("general", "notification", payload)
        channel, rest = payload.split(":", 1)
        subject, body = rest.split("|", 1)
        return channel.strip(), subject.strip(), body.strip()

    def _parse_email_payload(self, payload: str) -> tuple[str, str]:
        # very simple: subject:<subject> | <body>
        subject = "(no subject)"
        body = payload
        if "subject:" in payload and "|" in payload:
            _, rest = payload.split("subject:", 1)
            subject, body = rest.split("|", 1)
        return subject.strip(), body.strip()

    def _persist_notification(self, note: Notification) -> Path:
        NOTIFY_DIR.mkdir(parents=True, exist_ok=True)
        fname = f"{note.channel}_{note.subject.replace(' ', '_')}.txt"
        path = NOTIFY_DIR / fname
        path.write_text(note.serialize(), encoding="utf-8")
        return path
