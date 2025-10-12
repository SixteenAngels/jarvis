from __future__ import annotations

"""Face recognition interface with optional `face_recognition` dependency.

If `features.face_recognition` is enabled and the `face_recognition` package
is installed, returns basic face bounding boxes. Otherwise, returns an empty
list.
"""

from typing import List, Dict, Any
from ...utils.config import load_yaml


def _fr_available() -> bool:
    try:
        import face_recognition  # type: ignore
        _ = face_recognition
        return True
    except Exception:
        return False


def recognize_faces(image_path: str) -> List[Dict[str, Any]]:
    feats = load_yaml("/workspace/configs/features.yaml").get("features", {})
    if feats.get("face_recognition") and _fr_available():
        try:
            import face_recognition  # type: ignore

            img = face_recognition.load_image_file(image_path)
            boxes = face_recognition.face_locations(img)
            return [{"top": t, "right": r, "bottom": b, "left": l} for (t, r, b, l) in boxes]
        except Exception:
            pass
    return []
