from __future__ import annotations

"""Camera pipeline: capture frames, run detection/face recog, draw overlays.

This module provides a generator that yields JPEG frames suitable for MJPEG
streaming. It respects feature flags and gracefully degrades when providers are
not available.
"""

from typing import Dict, Any, Generator
import time

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None  # type: ignore

from ...utils.config import load_yaml
from .object_detect import detect_objects
from ...perception.goodseye.vision_for_security import security_detect
from .face_recog import recognize_faces


def iter_frames(source: str | int, target_fps: int = 5) -> Generator[bytes, None, None]:
    feats = load_yaml("/workspace/configs/features.yaml").get("features", {})
    if cv2 is None:
        return
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        return
    delay = 1.0 / max(1, target_fps)
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                time.sleep(delay)
                continue
            # Save to temp file for simplicity so object/face modules can read
            # Note: for performance, integrate directly on frame in the future
            ok2, jpg_buf = cv2.imencode('.jpg', frame)
            if not ok2:
                time.sleep(delay)
                continue
            tmp_path = '/tmp/frame.jpg'
            try:
                with open(tmp_path, 'wb') as f:
                    f.write(jpg_buf.tobytes())
                # Detection and face recog (Goodseye preferred when enabled)
                dets = []
                if feats.get('goodseye'):
                    try:
                        event = security_detect(tmp_path)
                        dets = event.get('detections', [])
                    except Exception:
                        dets = []
                if not dets and feats.get('yolo'):
                    dets = detect_objects(tmp_path)
                faces = recognize_faces(tmp_path) if feats.get('face_recognition') else []
                # Draw overlays
                try:
                    for d in dets:
                        bbox = d.get('bbox')
                        if bbox and len(bbox) == 4:
                            x1, y1, x2, y2 = map(int, bbox)
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(frame, d.get('object', '?'), (x1, max(0, y1-5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
                    for b in faces:
                        l = int(b.get('left', 0)); t = int(b.get('top', 0)); r = int(b.get('right', 0)); btm = int(b.get('bottom', 0))
                        cv2.rectangle(frame, (l, t), (r, btm), (255, 0, 0), 2)
                except Exception:
                    pass
                # Encode and yield
                ok3, out = cv2.imencode('.jpg', frame)
                if ok3:
                    yield out.tobytes()
            except Exception:
                pass
            time.sleep(delay)
    finally:
        try:
            cap.release()
        except Exception:
            pass
