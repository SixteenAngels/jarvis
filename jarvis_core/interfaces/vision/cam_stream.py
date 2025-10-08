from __future__ import annotations

"""Camera stream interface with OpenCV fallback.

If OpenCV is installed, opens a VideoCapture on the given URL/device index.
Otherwise returns simple stubs.
"""

from typing import Any

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None  # type: ignore


def open_stream(url: str | int) -> Any:
    if cv2 is None:
        return None
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        return None
    return cap


def read_frame(cap: Any) -> bytes | None:
    if cv2 is None or cap is None:
        return None
    ok, frame = cap.read()
    if not ok:
        return None
    ok, buf = cv2.imencode('.jpg', frame)
    return buf.tobytes() if ok else None
