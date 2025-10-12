## Module Index

This index summarizes each module’s responsibilities and source path.

### Core
- `core/kernel.py`: Orchestrator (Policy → Planner → Router → Agents → Reflection → Memory)
- `core/planner.py`: Goal decomposition; optional LLM outline
- `core/router.py`: Agent registry, routing, learning corrections persistence
- `core/reflection.py`: Output assessment and retry hints
- `core/policy.py`: Safety guardrails; base and emergency policies loader
- `core/memory/short_term.py`: Short-lived session memory buffer
- `core/memory/long_term.py`: Vector search memory with persistence
- `core/vectorstore/utils.py`: chunking/normalization helpers
- `core/vectorstore/faiss_index.py`: in-memory ANN using embedding adapter
- `core/vectorstore/persistent_index.py`: JSONL persistence, backups, locks
- `core/vectorstore/embedding.py`: Embedding adapter (SentenceTransformers fallback)
- `core/vectorstore/factory.py`: Selects backend (memory/FAISS/Annoy/persistent)
- `core/vectorstore/faiss_backend.py`: FAISS wrapper (if installed)
- `core/vectorstore/annoy_backend.py`: Annoy wrapper (if installed)
- `core/vectorstore/bm25.py`: BM25 keyword booster
- `core/vectorstore/meta_loader.py`: Reads meta.jsonl and groups by source
- `core/http_api.py`: Minimal HTTP server
- `core/http_api_fast.py`: FastAPI app (health, handle)

### Agents
- `agents/base.py`: Abstract base class for agents
- `agents/research.py`: Ingest/query, reranking, citations
- `agents/system.py`: Sandboxed commands; API run hints
- `agents/comms.py`: Notifications/email stubs
- `agents/biomedical.py`: Advisory-only triage suggestions
- `agents/electrical.py`: Ohm/LED, SPICE/ngspice simulate, KiCad DRC
- `agents/mechanical.py`: Deflection/gear calc, CAD (OpenSCAD/FreeCAD)
- `agents/civil.py`: Safety factor calculator
- `agents/software.py`: CLI scaffold generator
- `agents/engineering/software.py`: ComputerEngineer (analyze/lint/deps/scaffold)
- `agents/defense_agent.py`: Defensive log scanning and recommendations
- `agents/defense/cybersec.py`: SOC ingest + correlation
- `agents/defense/surveillance.py`: Vision-based detections stub
- `agents/defense/emergency.py`: ActionManager approvals flow
- `agents/robotics.py`: Simulated actions logger
- `agents/iot/home_assistant.py`: Home automation stub
- `agents/iot/energy_monitor.py`: Energy monitor stub
- `agents/iot/device_control.py`: Device control stub

### Interfaces
- `interfaces/speech/stt.py`: STT stub
- `interfaces/speech/tts.py`: TTS stub
- `interfaces/speech/voice_router.py`: Voice session flow
- `interfaces/vision/object_detect.py`: Object detection stub
- `interfaces/vision/face_recog.py`: Face recognition stub
- `interfaces/vision/cam_stream.py`: Camera streaming stub
- `interfaces/ar_vr/hud.py`: AR HUD overlay stub
- `interfaces/ar_vr/vr_display.py`: VR rendering stub

### Engineering tools
- `engineering/tools/spice_interface.py`: SPICE simulate stub
- `engineering/tools/ngspice_cli.py`: ngspice CLI fallback runner
- `engineering/tools/freecad_interface.py`: CAD stub generator
- `engineering/tools/openscad_cli.py`: OpenSCAD CLI fallback runner
- `engineering/tools/kicad_interface.py`: Netlist validation stub
- `engineering/tools/kicad_cli.py`: KiCad DRC CLI fallback runner

### Execution & Utils
- `execution/sandbox.py`: Whitelisted subprocess runner
- `execution/action_manager.py`: Approvals-enforced action requests
- `utils/logging.py`: Central logger
- `utils/config.py`: YAML loader with env substitution
- `utils/encryption.py`: Fernet/fallback encryption helpers
- `utils/signatures.py`: HMAC and optional RSA signing
- `infra/config_manager.py`: Profile loader/merger

### Examples
- `examples/run_research_agent.py`: Query via ResearchAgent
- `examples/run_cybersec_agent.py`: SOC ingest/correlation demo
- `examples/run_iot_controller.py`: IoT control stub usage
