## Jarvis Core — ASI with RAG and Multi-Agent System

Quickstart

- Install deps:
  - Python 3.11+
  - Full stack: pip install -r requirements.txt (installs AI/Vision/IoT/Robotics toolchain)
  - Optional extras (pip install -e .[vector,vision,stt_tts,mqtt,ros,defense])
- Optional system tools (for integrations):
  - ngspice (circuit simulation)
  - openscad (CAD generation)
  - kicad-cli/pcbnew (PCB DRC)
  - freecad (CAD workflows)
  - suricata, zeek (defensive SOC ingestion)
  - ffmpeg (media handling), mosquitto-clients (MQTT)
  - Install helper: scripts/install_tools.sh (Debian/Ubuntu)

Environment variables (common):
- API_TOKEN: bearer token for API auth
- ELEVENLABS_API_KEY: enable ElevenLabs TTS when features.tts_elevenlabs=true
- AZURE_SPEECH_KEY / AZURE_SPEECH_REGION: enable Azure TTS when features.tts_azure=true
- Run tests:
  - PYTHONPATH=. pytest -q
- CLI:
  - python -m jarvis_core.cli "ingest /path/to/docs"
  - python -m jarvis_core.cli "query design notes"

## Run on all platforms

### Linux/Mac (native)
- Python runtime:
  - export API_TOKEN=changeme-token
  - pip install -r requirements.txt
  - python main.py --api --host 0.0.0.0 --port 8000
  - TLS (optional): python main.py --api --host 0.0.0.0 --port 8443 --ssl-certfile cert.pem --ssl-keyfile key.pem
  - Open http://localhost:8000/ (3-button launcher)
- Jarvis UI → provides Command runner, Camera stream, Feed Knowledge uploader, Defense summary
- Docker runtime:
  - docker compose up --build
  - Prometheus http://localhost:9090; Grafana http://localhost:3000 (admin/admin)

### Windows
- Use WSL2 for best compatibility:
  - Install Docker Desktop or run Python in WSL2
  - pip install -r requirements.txt
  - python main.py --api --host 0.0.0.0 --port 8000
  - Or: docker compose up --build

### GPU detection
- Embeddings auto-detect CUDA (torch.cuda.is_available) and use GPU if present, else CPU.
- YOLO model selection is CPU by default; set ULTRALYTICS settings as needed.

### Environment
- API_TOKEN: bearer token for API auth
- OPENAI_API_KEY: enable cloud LLMs when available
- ELEVENLABS_API_KEY / AZURE_SPEECH_KEY / AZURE_SPEECH_REGION for TTS providers
- SIGNING_KEY or PUBLIC_KEY (PEM) for signed approvals when features.signed_approvals=true

## HTTP API
- /health: service health
- /handle: POST {command, context}
- /rag/reembed: POST {persist_dir, backend}
- /rag/stats: vectorstore stats (meta lines, index presence)
- /rag/upload: POST multipart files to ingest (PDF/TXT/MD)
- /rag/ingest_url: POST form {url} to fetch and ingest
- /rag/crawl: POST form {seed, depth} same-host web crawl and ingest
- /vision/frame: single JPEG frame; /vision/stream: MJPEG stream
- /iot/discover: MQTT/ROS discovery snapshot
- /defense/summary: counts by source and severity; risk score
- /defense/stream: SSE live SOC lines (Suricata/Wazuh)
- /metrics: Prometheus exposition (optional dependency)
- / (web UI): buttons to install requirements, open Jarvis UI, and exit

## Production runbook highlights
- Logging: structured JSON to stdout + rotating file at /workspace/data/logs/jarvis.log
- Rate limiting: sliding window with periodic reset (configure in configs/features.yaml)
- RAG: FAISS/Annoy save/load, re-embed endpoint, backups/locks for JSONL persistence
- Sandbox: CPU/mem quotas, per-task workspace, rollback archives
- Security: policy guardrails, approvals; optional signed approvals (HMAC/RSA)

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
