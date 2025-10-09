from __future__ import annotations

"""Object detection interface with YOLOv8 fallback stubs.

If `features.yolo` is enabled and `ultralytics` is installed, runs YOLOv8.
Otherwise returns a placeholder detection.
"""

from typing import List, Dict, Any
from ...utils.config import load_yaml


def _yolo_available() -> bool:
    try:
        import ultralytics  # type: ignore
        _ = ultralytics
        return True
    except Exception:
        return False


def detect_objects(image_path: str) -> List[Dict[str, Any]]:
    feats = load_yaml("/workspace/configs/features.yaml").get("features", {})
    if feats.get("yolo") and _yolo_available():
        try:
            from ultralytics import YOLO  # type: ignore

            model = YOLO("yolov8n.pt")
            results = model.predict(image_path, verbose=False)
            detections: List[Dict[str, Any]] = []
            for r in results:
                for b in r.boxes:
                    cls = int(b.cls[0])
                    conf = float(b.conf[0])
                    name = model.names.get(cls, str(cls))
                    try:
                        xyxy = b.xyxy[0].tolist()  # [x1,y1,x2,y2]
                    except Exception:
                        xyxy = None
                    item: Dict[str, Any] = {"object": name, "confidence": conf}
                    if xyxy:
                        item["bbox"] = xyxy
                    detections.append(item)
            return detections
        except Exception:
            pass
    return [{"object": "person", "confidence": 0.5}]
