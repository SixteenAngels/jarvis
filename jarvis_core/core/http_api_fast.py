from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any

from .kernel import Kernel

app = FastAPI(title="Jarvis Core API")
_kernel = Kernel()

class HandleRequest(BaseModel):
    command: str
    context: Dict[str, Any] | None = None

@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.post("/handle")
async def handle(req: HandleRequest) -> Dict[str, Any]:
    return _kernel.handle(req.command, req.context or {})
