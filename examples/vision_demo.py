"""
Example: Vision demo with YOLO object detection and face recognition.

Usage:
  python examples/vision_demo.py --image /path/to/image.jpg

If features.yolo or features.face_recognition are disabled or packages are
missing, outputs fall back gracefully.
"""
from __future__ import annotations

import argparse
from jarvis_core.interfaces.vision.object_detect import detect_objects
from jarvis_core.interfaces.vision.face_recog import recognize_faces


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    args = parser.parse_args()

    dets = detect_objects(args.image)
    faces = recognize_faces(args.image)
    print({"objects": dets, "faces": faces})


if __name__ == "__main__":
    main()
