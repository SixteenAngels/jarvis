from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException, Request, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Deque
from collections import deque
import time
import os
import asyncio

from .kernel import Kernel
from ..utils.config import load_yaml
from ..utils.logging import get_logger
from ..agents.research import ResearchAgent
from ..interfaces.vision import cam_stream
from ..iot.discovery import discover_mqtt, discover_ros
import uuid

_features = load_yaml("/workspace/configs/features.yaml").get("features", {})
_api_token = os.getenv("API_TOKEN") or _features.get("api_auth_token")
_rate_limit = int(_features.get("rate_limit_per_min", 0))

app = FastAPI(title="Jarvis Core API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
_kernel = Kernel()
_logger = get_logger("api")

class HandleRequest(BaseModel):
    command: str
    context: Dict[str, Any] | None = None


class ReembedRequest(BaseModel):
    persist_dir: str | None = None
    backend: str | None = None

@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}

class RateLimiter:
    def __init__(self, per_minute: int) -> None:
        self.per_minute = max(0, per_minute)
        self.window: Deque[float] = deque()

    def allow(self) -> bool:
        if not self.per_minute:
            return True
        now = time.time()
        # prune entries older than 60s
        while self.window and now - self.window[0] > 60:
            self.window.popleft()
        if len(self.window) >= self.per_minute:
            return False
        self.window.append(now)
        return True

    def reset(self) -> None:
        self.window.clear()


_limiter = RateLimiter(_rate_limit)


@app.on_event("startup")
async def _startup_preflight() -> None:
    # Log a quick capability report
    feats = _features
    _logger.info(f"Features enabled: {feats}")


@app.on_event("startup")
async def _limiter_reset_task() -> None:
    # Periodically reset the limiter window once per minute
    async def _run():
        while True:
            await asyncio.sleep(60)
            _limiter.reset()
            _logger.info("rate_limiter_reset")

    asyncio.create_task(_run())


@app.post("/handle")
async def handle(req: HandleRequest, authorization: str | None = Header(default=None)) -> Dict[str, Any]:
    # Simple token auth
    if _api_token and authorization != f"Bearer {_api_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Simple in-memory rate limit (reset not implemented; for demo only)
    if not _limiter.allow():
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    # Audit log
    rid = str(uuid.uuid4())
    try:
        _logger.info(f"request_id={rid} command={req.command}")
    except Exception:
        pass
    resp = _kernel.handle(req.command, req.context or {})
    try:
        # append audit artifact non-destructively
        artifacts = resp.get("artifacts", [])
        artifacts.append({"type": "audit", "request_id": rid})
        resp["artifacts"] = artifacts
    except Exception:
        pass
    return resp


@app.post("/rag/reembed")
async def rag_reembed(req: ReembedRequest, authorization: str | None = Header(default=None)) -> Dict[str, Any]:
    # Auth
    if _api_token and authorization != f"Bearer {_api_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Determine persist_dir and backend
    cfg = load_yaml("/workspace/configs/vectorstore.yaml")
    persist_dir = req.persist_dir or cfg.get("persist_dir", "/workspace/data/vectorstore")
    backend = (req.backend or cfg.get("backend", "memory")).lower()
    try:
        agent = ResearchAgent(persist_dir=persist_dir, backend=backend)
        # Re-embed entire index and save
        agent._reembed_index()  # type: ignore[attr-defined]
        if getattr(agent, "_persist_dir", None):
            try:
                agent.index.save(agent._persist_dir)  # type: ignore[attr-defined]
            except Exception:
                pass
        return {"status": "ok", "result": f"reembedded backend={backend} dir={persist_dir}", "artifacts": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"reembed_failed: {e}")


@app.get("/vision/frame")
async def get_frame(source: str = Query(default="0")) -> Response:
    # No auth gate for basic frame; add if desired
    # Try to parse numeric device index
    try:
        src: int | str = int(source)
    except Exception:
        src = source
    cap = cam_stream.open_stream(src)
    data = cam_stream.read_frame(cap)
    try:
        # release if available
        if hasattr(cap, "release"):
            cap.release()  # type: ignore[attr-defined]
    except Exception:
        pass
    if not data:
        raise HTTPException(status_code=503, detail="camera_unavailable")
    return Response(content=data, media_type="image/jpeg")


@app.get("/iot/discover")
async def iot_discover(mqtt_broker: str = Query(default="localhost"), ros_host: str = Query(default="localhost"), ros_port: int = Query(default=9090)) -> Dict[str, Any]:
    mqtt_info = discover_mqtt(mqtt_broker)
    ros_info = discover_ros(ros_host, ros_port)
    return {"mqtt": mqtt_info, "ros": ros_info}
