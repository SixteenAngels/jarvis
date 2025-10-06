from __future__ import annotations

import time
from typing import Dict, Any, List

# Placeholder for a real Goodseye detector import
# from perception.goodseye.detector import detect

def _mock_detect(image_path: str) -> List[Dict[str, Any]]:
    # Minimal mock detections
    return [
        {"object": "person", "confidence": 0.8, "bbox": [10, 10, 100, 150]},
        {"object": "car", "confidence": 0.7, "bbox": [200, 50, 300, 150]},
    ]


def security_detect(image_path: str) -> Dict[str, Any]:
    # Replace _mock_detect with real Goodseye detector when integrated
    dets = _mock_detect(image_path)
    timestamp = time.time()
    security_objs = [d for d in dets if d.get("object") in ("person", "car", "truck", "backpack", "suitcase")]
    event = {
        "timestamp": timestamp,
        "image": image_path,
        "detections": security_objs,
    }
    return event
