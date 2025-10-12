from __future__ import annotations

import os
import time
from typing import Dict, Any, List

# Goodseye detector integration with graceful fallback
try:  # pragma: no cover - optional dependency
    from goodseye import Detector as GoodseyeDetector  # type: ignore
except Exception:  # pragma: no cover
    GoodseyeDetector = None  # type: ignore

from ...utils.config import load_yaml


def _mock_detect(image_path: str) -> List[Dict[str, Any]]:
    return [
        {"object": "person", "confidence": 0.8, "bbox": [10, 10, 100, 150]},
        {"object": "car", "confidence": 0.7, "bbox": [200, 50, 300, 150]},
    ]


def _fallback_detect(image_path: str) -> List[Dict[str, Any]]:
    try:
        from ...interfaces.vision.object_detect import detect_objects
        return detect_objects(image_path)
    except Exception:
        return _mock_detect(image_path)


def security_detect(image_path: str) -> Dict[str, Any]:
    dets: List[Dict[str, Any]]
    feats = {}
    try:
        feats = load_yaml("/workspace/configs/features.yaml").get("features", {})
    except Exception:
        feats = {}
    use_goodseye = feats.get("goodseye", True)
    if use_goodseye and GoodseyeDetector is not None:
        try:
            model_path = os.getenv("GOODSEYE_MODEL")
            detector = GoodseyeDetector(model_path) if model_path else GoodseyeDetector()  # type: ignore[call-arg]
            results = detector.detect(image_path)
            dets = []
            for r in results or []:
                # Support dict-like or object-like result items
                try:
                    label = getattr(r, "label", None) or getattr(r, "class_name", None) or r.get("label") or r.get("object")  # type: ignore[attr-defined]
                except Exception:
                    label = "object"
                try:
                    conf = float(getattr(r, "score", None) or getattr(r, "confidence", None) or r.get("confidence", 0.0))  # type: ignore[attr-defined]
                except Exception:
                    conf = 0.0
                bbox = None
                try:
                    b = getattr(r, "bbox", None) or getattr(r, "xyxy", None) or r.get("bbox") or r.get("xyxy")  # type: ignore[attr-defined]
                    if isinstance(b, (list, tuple)) and len(b) == 4:
                        bbox = [float(x) for x in b]
                except Exception:
                    bbox = None
                item: Dict[str, Any] = {"object": str(label), "confidence": conf}
                if bbox:
                    item["bbox"] = bbox
                dets.append(item)
        except Exception:
            dets = _fallback_detect(image_path)
    else:
        dets = _fallback_detect(image_path)
    timestamp = time.time()
    allow = {"person", "car", "truck", "backpack", "suitcase"}
    security_objs = [d for d in dets if str(d.get("object")).lower() in allow]
    event = {
        "timestamp": timestamp,
        "image": image_path,
        "detections": security_objs,
    }
    return event
