from __future__ import annotations

from typing import Dict, Any, List

from .base import BaseAgent


DISCLAIMER = (
    "This system is advisory only and not a substitute for professional medical advice. "
    "Always consult a qualified clinician for diagnosis and treatment decisions."
)


class BiomedicalAgent(BaseAgent):
    name: str = "biomedical"
    intents: List[str] = [
        "medical",
        "biomedical",
        "symptom",
        "triage",
        "health",
        "advice",
    ]

    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        query = task.strip()
        # Very basic rule-based triage suggestions; always includes disclaimer
        advice_lines: List[str] = [DISCLAIMER]
        lower = query.lower()
        if any(k in lower for k in ["chest pain", "shortness of breath", "stroke", "unconscious"]):
            advice_lines.append("Potential emergency indicators detected. Call emergency services immediately.")
        elif any(k in lower for k in ["fever", "cough", "sore throat", "flu"]):
            advice_lines.append("Consider rest, hydration, and fever management per OTC guidance. Monitor symptoms.")
            advice_lines.append("Seek medical evaluation if symptoms worsen or persist beyond 48-72 hours.")
        elif any(k in lower for k in ["headache", "migraine"]):
            advice_lines.append("Reduce light/noise exposure and consider appropriate analgesics if safe for you.")
        else:
            advice_lines.append("Collect more details: onset, duration, severity, associated symptoms, medications, allergies.")
        return {"status": "ok", "result": "\n".join(advice_lines), "artifacts": []}
