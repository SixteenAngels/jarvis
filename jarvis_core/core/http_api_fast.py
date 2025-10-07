from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from .kernel import Kernel
from ..utils.config import load_yaml

_features = load_yaml("/workspace/configs/features.yaml").get("features", {})
_api_token = _features.get("api_auth_token")
_rate_limit = int(_features.get("rate_limit_per_min", 0))

app = FastAPI(title="Jarvis Core API")
_kernel = Kernel()

class HandleRequest(BaseModel):
    command: str
    context: Dict[str, Any] | None = None

@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}

_requests_in_window = 0


@app.post("/handle")
async def handle(req: HandleRequest, authorization: str | None = Header(default=None)) -> Dict[str, Any]:
    # Simple token auth
    if _api_token and authorization != f"Bearer {_api_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Simple in-memory rate limit (reset not implemented; for demo only)
    global _requests_in_window
    if _rate_limit and _requests_in_window >= _rate_limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    _requests_in_window += 1
    return _kernel.handle(req.command, req.context or {})
