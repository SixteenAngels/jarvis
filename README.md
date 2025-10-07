## Jarvis Core — ASI with RAG and Multi-Agent System

Quickstart

- Install deps:
  - Python 3.11+
  - Minimal: pip install -r requirements.txt (base runtime)
  - Full stack: pip install -r requirements/full.txt (installs AI/Vision/IoT/Robotics toolchain)
- Optional system tools (for integrations):
  - ngspice (circuit simulation)
  - openscad (CAD generation)
  - kicad-cli/pcbnew (PCB DRC)
  - freecad (CAD workflows)
  - suricata, zeek (defensive SOC ingestion)
  - ffmpeg (media handling), mosquitto-clients (MQTT)
  - Install helper: scripts/install_tools.sh (Debian/Ubuntu)
- Run tests:
  - PYTHONPATH=. pytest -q
- CLI:
  - python -m jarvis_core.cli "ingest /path/to/docs"
  - python -m jarvis_core.cli "query design notes"

Key components

- Core: `core/kernel.py`, `core/planner.py`, `core/reflection.py`, `core/policy.py`
- Memory: `core/memory/{short_term.py,long_term.py}`
- RAG: `core/vectorstore` (in-memory + persistent), embedding adapter with SentenceTransformers fallback
- Agents: research, system, comms, biomedical, electrical, mechanical, software, defense, robotics, civil
- Defense integrations (defensive-only): Suricata/Zeek ingest, correlator, Goodseye adapter

Configuration

- Policy: `configs/policy.yaml` supports custom `block_keywords`
- Defense: `configs/defense_integrations.yaml`

Examples

- Ingest and query:
  - python -m jarvis_core.cli "ingest ./docs"
  - python -m jarvis_core.cli "query pcb design"
- System (sandboxed):
  - python -m jarvis_core.cli "run: echo hello"
- Notifications:
  - python -m jarvis_core.cli "notify ops: Deploy | Success"

Notes

- Offensive capabilities are disallowed by policy and design. Defense features are strictly for detection, correlation, and response with approvals.
- Replace mock vision with your Goodseye detector and configure real Suricata/Zeek paths for SOC correlation.
