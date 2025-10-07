#!/usr/bin/env bash
set -euo pipefail

# Quick installer for system tools used by Jarvis Core (Ubuntu/Debian)
# NOTE: Requires sudo privileges.

sudo apt-get update
sudo apt-get install -y \
  ngspice \
  openscad \
  kicad \
  freecad \
  suricata \
  zeek \
  ffmpeg \
  mosquitto-clients

# Optional Python extras (install with pip if desired):
# pip install faiss-cpu annoy opencv-python pyttsx3 vosk

echo "System tools installation attempted. Some packages may not exist on all distros."