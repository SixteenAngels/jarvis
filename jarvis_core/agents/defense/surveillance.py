from __future__ import annotations

from typing import Dict, Any

from ..base import BaseAgent
from ...perception.goodseye.vision_for_security import security_detect
from ...interfaces.vision.object_detect import detect_objects


class SurveillanceAgent(BaseAgent):
    name: str = "surveillance"
    intents = ["surveillance", "camera", "monitor"]

    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        img = context.get("image", "frame.jpg")
        try:
            event = security_detect(img)
            dets = event.get("detections", [])
        except Exception:
            dets = detect_objects(img)
        return {"status": "ok", "result": f"{len(dets)} detections", "artifacts": [{"type": "detections", "items": dets}]}
