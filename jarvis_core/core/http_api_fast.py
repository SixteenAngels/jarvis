from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Deque
from collections import deque
import time

from .kernel import Kernel
from ..utils.config import load_yaml
from ..utils.logging import get_logger

_features = load_yaml("/workspace/configs/features.yaml").get("features", {})
_api_token = _features.get("api_auth_token")
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


_limiter = RateLimiter(_rate_limit)


@app.on_event("startup")
async def _startup_preflight() -> None:
    # Log a quick capability report
    feats = _features
    _logger.info(f"Features enabled: {feats}")


@app.post("/handle")
async def handle(req: HandleRequest, authorization: str | None = Header(default=None)) -> Dict[str, Any]:
    # Simple token auth
    if _api_token and authorization != f"Bearer {_api_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Simple in-memory rate limit (reset not implemented; for demo only)
    if not _limiter.allow():
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return _kernel.handle(req.command, req.context or {})
