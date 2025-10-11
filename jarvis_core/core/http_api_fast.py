from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException, Request, Response, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Deque
from collections import deque
import time
import os
import asyncio
import threading
import subprocess

from .kernel import Kernel
from ..utils.config import load_yaml
from ..utils.logging import get_logger
from ..agents.research import ResearchAgent
from ..interfaces.vision import cam_stream
from ..iot.discovery import discover_mqtt, discover_ros
import uuid
from ..interfaces.vision.pipeline import iter_frames

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
_install_running = False
_install_log = "/workspace/data/logs/install.log"

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


@app.post("/rag/upload")
async def rag_upload(authorization: str | None = Header(default=None), files: list[UploadFile] = File(...)) -> Dict[str, Any]:
    if _api_token and authorization != f"Bearer {_api_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    cfg = load_yaml("/workspace/configs/vectorstore.yaml")
    persist_dir = cfg.get("persist_dir", "/workspace/data/vectorstore")
    backend = (cfg.get("backend", "memory")).lower()
    # Save uploads to disk and ingest
    saved: list[str] = []
    try:
        os.makedirs(persist_dir, exist_ok=True)
    except Exception:
        pass
    uploads_dir = "/workspace/data/uploads"
    os.makedirs(uploads_dir, exist_ok=True)
    for uf in files:
        try:
            dest = os.path.join(uploads_dir, uf.filename)
            with open(dest, "wb") as f:
                f.write(await uf.read())
            saved.append(dest)
        except Exception:
            continue
    agent = ResearchAgent(persist_dir=persist_dir, backend=backend)
    total_chunks = 0
    for p in saved:
        try:
            res = agent.execute(f"ingest {p}", {})
            # parse number from result text conservatively
            total_chunks += int(res.get("result", "0").split(" ")[1]) if res.get("result") else 0
        except Exception:
            continue
    try:
        if getattr(agent, "_persist_dir", None):
            agent.index.save(agent._persist_dir)  # type: ignore[attr-defined]
    except Exception:
        pass
    return {"status": "ok", "result": f"uploaded={len(saved)} ingested_chunks≈{total_chunks}", "artifacts": [{"type": "uploads", "items": saved}]}


@app.post("/rag/ingest_url")
async def rag_ingest_url(authorization: str | None = Header(default=None), url: str = Form(...)) -> Dict[str, Any]:
    if _api_token and authorization != f"Bearer {_api_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        import requests  # type: ignore
        resp = requests.get(url, timeout=10)
        if resp.status_code >= 400:
            raise HTTPException(status_code=400, detail="fetch_failed")
        # Write to a temp file and ingest
        uploads_dir = "/workspace/data/uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        fname = os.path.join(uploads_dir, "web_ingest.txt")
        with open(fname, "w", encoding="utf-8") as f:
            f.write(resp.text)
        cfg = load_yaml("/workspace/configs/vectorstore.yaml")
        persist_dir = cfg.get("persist_dir", "/workspace/data/vectorstore")
        backend = (cfg.get("backend", "memory")).lower()
        agent = ResearchAgent(persist_dir=persist_dir, backend=backend)
        agent.execute(f"ingest {fname}", {})
        try:
            if getattr(agent, "_persist_dir", None):
                agent.index.save(agent._persist_dir)  # type: ignore[attr-defined]
        except Exception:
            pass
        return {"status": "ok", "result": "url_ingested", "artifacts": [{"type": "source", "url": url, "path": fname}]}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="ingest_url_failed")


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


@app.get("/vision/stream")
async def get_stream(source: str = Query(default="0")) -> Response:
    # Simple MJPEG stream. For production, consider uvicorn.stream or websockets.
    try:
        src: int | str = int(source)
    except Exception:
        src = source
    boundary = "frame"
    async def _gen():  # type: ignore
        for frame in iter_frames(src, target_fps=5):
            yield b"--" + boundary.encode() + b"\r\n"
            yield b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
    return Response(content=_gen(), media_type=f"multipart/x-mixed-replace; boundary={boundary}")


@app.get("/iot/discover")
async def iot_discover(mqtt_broker: str = Query(default="localhost"), ros_host: str = Query(default="localhost"), ros_port: int = Query(default=9090)) -> Dict[str, Any]:
    mqtt_info = discover_mqtt(mqtt_broker)
    ros_info = discover_ros(ros_host, ros_port)
    return {"mqtt": mqtt_info, "ros": ros_info}


# ------------------------ Minimal UI ------------------------

def _html_page(body: str) -> Response:
    html = f"""
<!doctype html>
<html><head><meta charset='utf-8'><title>Jarvis Core</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 2rem; }}
button {{ padding: 0.6rem 1rem; margin: 0.3rem; }}
textarea, input {{ width: 100%; margin: 0.3rem 0; }}
.row {{ margin: 1rem 0; }}
</style>
</head><body>
{body}
</body></html>
"""
    return Response(content=html, media_type="text/html")


@app.get("/")
async def ui_index() -> Response:
    body = """
<h1>Jarvis Core</h1>
<div class='row'>
  <form action='/ui/install' method='post' style='display:inline'>
    <button type='submit'>Install Requirements</button>
  </form>
  <a href='/ui/jarvis'><button>Open Jarvis UI</button></a>
  <form action='/ui/exit' method='post' style='display:inline'>
    <button type='submit' style='background:#e33;color:#fff'>Exit</button>
  </form>
</div>
"""
    return _html_page(body)


def _run_install_bg() -> None:
    global _install_running
    _install_running = True
    os.makedirs(os.path.dirname(_install_log), exist_ok=True)
    try:
        with open(_install_log, "w", encoding="utf-8") as f:
            proc = subprocess.Popen(["python", "-m", "pip", "install", "-r", "/workspace/requirements.txt"], stdout=f, stderr=subprocess.STDOUT)
            proc.wait()
    finally:
        _install_running = False


@app.post("/ui/install")
async def ui_install() -> Response:
    if not _install_running:
        threading.Thread(target=_run_install_bg, daemon=True).start()
    body = """
<h2>Installing requirements...</h2>
<p>Logs will appear below (refresh to update):</p>
<pre style='white-space:pre-wrap;'>
"""
    try:
        with open(_install_log, "r", encoding="utf-8") as f:
            body += f.read()
    except Exception:
        body += "(log not available yet)"
    body += "</pre><p><a href='/'>Back</a></p>"
    return _html_page(body)


@app.get("/ui/jarvis")
async def ui_jarvis() -> Response:
    body = """
<h2>Jarvis UI</h2>
<div class='row'>
<form id='cmdForm'>
  <label>Command</label>
  <input id='cmd' placeholder='query alpha' />
  <button type='submit'>Run</button>
</form>
<pre id='out'></pre>
</div>
<div class='row'>
  <h3>Camera Stream</h3>
  <img src='/vision/stream' width='480'/>
</div>
<div class='row'>
  <h3>Feed Knowledge</h3>
  <form id='uploadForm' enctype='multipart/form-data'>
    <label>Upload files (PDF, TXT, MD)</label>
    <input id='files' name='files' type='file' multiple />
    <button type='submit'>Upload & Ingest</button>
  </form>
  <form id='urlForm' method='post'>
    <label>Ingest from URL</label>
    <input id='urlInput' name='url' placeholder='https://example.com/guide' />
    <button type='submit'>Fetch & Ingest</button>
  </form>
  <pre id='ingestOut'></pre>
</div>
<script>
const form = document.getElementById('cmdForm');
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const cmd = document.getElementById('cmd').value;
  const resp = await fetch('/handle', {method: 'POST', headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + (localStorage.getItem('API_TOKEN')||'')}, body: JSON.stringify({command: cmd})});
  const data = await resp.json();
  document.getElementById('out').textContent = JSON.stringify(data, null, 2);
});

// File upload ingest
const uploadForm = document.getElementById('uploadForm');
uploadForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData();
  const files = document.getElementById('files').files;
  for (const f of files) fd.append('files', f);
  const resp = await fetch('/rag/upload', { method: 'POST', headers: { 'Authorization': 'Bearer ' + (localStorage.getItem('API_TOKEN')||'') }, body: fd });
  const data = await resp.json();
  document.getElementById('ingestOut').textContent = JSON.stringify(data, null, 2);
});

// URL ingest
const urlForm = document.getElementById('urlForm');
urlForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const url = document.getElementById('urlInput').value;
  const fd = new FormData();
  fd.append('url', url);
  const resp = await fetch('/rag/ingest_url', { method: 'POST', headers: { 'Authorization': 'Bearer ' + (localStorage.getItem('API_TOKEN')||'') }, body: fd });
  const data = await resp.json();
  document.getElementById('ingestOut').textContent = JSON.stringify(data, null, 2);
});
</script>
"""
    return _html_page(body)


@app.post("/ui/exit")
async def ui_exit() -> Response:
    def _shutdown():
        time.sleep(0.5)
        os._exit(0)
    threading.Thread(target=_shutdown, daemon=True).start()
    return _html_page("<h2>Shutting down...</h2>")
