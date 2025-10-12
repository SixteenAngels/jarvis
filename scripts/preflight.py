#!/usr/bin/env python3
from __future__ import annotations

import importlib
import shutil
import json
from pathlib import Path

CFG = Path("/workspace/configs/features.yaml")

OPTIONAL = {
    "whisper": ("openai_whisper", None),
    "yolo": ("ultralytics", None),
    "faiss": ("faiss", None),
    "annoy": ("annoy", None),
    "cross_encoder": ("sentence_transformers", None),
    "mqtt": ("paho.mqtt.client", None),
    "ros2": ("roslibpy", None),
}

TOOLS = {
    "ngspice": "ngspice",
    "openscad": "openscad",
    "kicad-cli": "kicad-cli",
}


def has_module(name: str) -> bool:
    try:
        importlib.import_module(name)
        return True
    except Exception:
        return False


def has_tool(name: str) -> bool:
    return shutil.which(name) is not None


def main() -> None:
    report = {"modules": {}, "tools": {}}
    for key, (mod, _) in OPTIONAL.items():
        report["modules"][key] = has_module(mod)
    for key, exe in TOOLS.items():
        report["tools"][key] = bool(has_tool(exe))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
