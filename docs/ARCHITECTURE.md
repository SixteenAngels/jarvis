## Jarvis Core — Architecture Overview

This document explains the major subsystems of Jarvis Core, how data flows through the system, and how to extend the platform with new agents and integrations.

### High-level diagram

```
User/Apps (CLI, HTTP, Voice)
        │
        ▼
+------------------+      +------------------+
|  Policy Engine   |◀───▶ |  Approvals/AM   |
|  (safety/ethics) |      |  (ActionManager) |
+------------------+      +------------------+
        │
        ▼
+------------------+      +------------------+      +------------------+
|     Planner      | ───▶ |      Router      | ───▶ |     Agents       |
| (task breakdown) |      | (agent selection)|      | (domain experts) |
+------------------+      +------------------+      +------------------+
        ▲                         │                         │
        │                         ▼                         │
        │                +------------------+               │
        │                |   Reflection     | ──────────────┘
        │                | (self-evaluation)|
        │                +------------------+
        │                         │
        │                         ▼
        │                +------------------+
        └─────────────── |     Memory       |
                         | (short + long)   |
                         +------------------+
```

- Policy blocks unsafe requests before planning or execution.
- Planner converts user goals into a sequence of steps.
- Router chooses an agent for each step, with learning feedback.
- Agents may use RAG (vectorstore) for factual grounding and tools for deterministic tasks.
- Reflection assesses results and can request retries or re-planning.
- Memory persists short-term session context and long-term semantic artifacts.

### Core packages
- `core/kernel.py`: orchestrates Policy → Planner → Router → Agents → Reflection → Memory.
- `core/planner.py`: decomposes goals into actionable steps, optionally using an LLM.
- `core/router.py`: ranks/candidates agents and dispatches tasks. Persists corrections for learning.
- `core/reflection.py`: reviews agent outputs, suggests retry parameters.
- `core/policy.py`: safety guardrails; loads base and emergency policies.
- `core/memory/`: short-term ring buffer and long-term vector memory.
- `core/vectorstore/`: embedding adapter, in-memory + persistent indices, FAISS/Annoy wrappers, chunking utils, BM25.

### RAG + Vectorstore
- Embeddings via `EmbeddingAdapter` (SentenceTransformers fallback; cloud possible).
- Index backends: in-memory, JSONL persistent, FAISS/Annoy (with graceful fallback if not installed).
- Ranking pipeline: overlap chunking → ANN retrieval → MMR diversity → BM25 keyword boost → deduped citations with snippets.
- Persistence writes append-only metadata and versioned backups; file locks reduce race conditions.

### Agents
- Research: ingest/query with citations and reranking; PDF extraction (if pypdf available).
- System: sandboxed shell with whitelists; API run hints.
- Comms: notifications stubs, artifact persistence.
- Engineering: Electrical (Ohm/LED; SPICE/ngspice; KiCad DRC), Mechanical (beam/gear; OpenSCAD/FreeCAD), Civil, Biomedical, Software, ComputerEngineer.
- Defense: log ingestion (Suricata/Zeek), correlation, honeypot/cuckoo stubs, surveillance/emergency stubs.
- Robotics/IoT: basic stubs; logging/bridging points.

### Interfaces
- Speech (STT/TTS) stubs, Voice Router.
- Vision (object/face/camera) stubs.
- AR/VR (HUD/VR) stubs.

### HTTP/API
- `core/http_api_fast.py` (FastAPI) exposes `/health`, `/handle` for command execution via Kernel.
- Token/rate-limit hooks (to be enabled via `configs/features.yaml`).

### Extending the system
- Add a new agent by subclassing `agents.base.BaseAgent` and registering (or letting Router discover/register).
- If the agent needs RAG, depend on `core/vectorstore` and follow the Research agent pattern.
- Declare intents/keywords that help Router’s can_handle() and learning weights choose the agent.
- Log artifacts and results; Reflection and Memory will capture outputs and help future tasks.

### Notes
- The codebase emphasizes security defaults: policy checks, sandboxed execution, approvals, and defensive SOC integrations.
- Offensive cyber tooling is out of scope; red-team emulation for testing should be isolated and permissioned.
