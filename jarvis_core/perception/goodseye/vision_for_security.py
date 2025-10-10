from __future__ import annotations

import time
from typing import Dict, Any, List

# Goodseye detector integration with graceful fallback
try:  # pragma: no cover - optional dependency
    from goodseye import Detector as GoodseyeDetector  # type: ignore
except Exception:  # pragma: no cover
    GoodseyeDetector = None  # type: ignore

def _mock_detect(image_path: str) -> List[Dict[str, Any]]:
    return [
        {"object": "person", "confidence": 0.8, "bbox": [10, 10, 100, 150]},
        {"object": "car", "confidence": 0.7, "bbox": [200, 50, 300, 150]},
    ]


def security_detect(image_path: str) -> Dict[str, Any]:
    dets: List[Dict[str, Any]]
    if GoodseyeDetector is not None:
        try:
            detector = GoodseyeDetector()
            results = detector.detect(image_path)
            dets = []
            for r in results or []:
                item: Dict[str, Any] = {
                    "object": r.get("label") or r.get("object") or "object",
                    "confidence": float(r.get("confidence", 0.0)),
                }
                bbox = r.get("bbox") or r.get("xyxy")
                if bbox and isinstance(bbox, (list, tuple)) and len(bbox) == 4:
                    item["bbox"] = [float(x) for x in bbox]
                dets.append(item)
        except Exception:
            dets = _mock_detect(image_path)
    else:
        dets = _mock_detect(image_path)
    timestamp = time.time()
    security_objs = [d for d in dets if d.get("object") in ("person", "car", "truck", "backpack", "suitcase")]
    event = {
        "timestamp": timestamp,
        "image": image_path,
        "detections": security_objs,
    }
    return event
