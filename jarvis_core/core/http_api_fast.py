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
from ..defense.risk import score_events
import uuid
from ..interfaces.vision.pipeline import iter_frames
from ..defense.risk import score_events

_features = load_yaml("/workspace/configs/features.yaml").get("features", {})
_api_token = os.getenv("API_TOKEN") or _features.get("api_auth_token")
_rate_limit = int(_features.get("rate_limit_per_min", 0))

# Optional Prometheus metrics (do not hard-require dependency)
try:  # pragma: no cover - optional
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST  # type: ignore
except Exception:  # pragma: no cover
    Counter = None  # type: ignore
    Histogram = None  # type: ignore
    generate_latest = None  # type: ignore
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"

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

if Counter is not None:
    REQ_COUNT = Counter("jarvis_requests_total", "Total API requests", ["endpoint"])  # type: ignore
    REQ_LATENCY = Histogram("jarvis_request_seconds", "API request latency", ["endpoint"])  # type: ignore
else:
    REQ_COUNT = None
    REQ_LATENCY = None

class HandleRequest(BaseModel):
    command: str
    context: Dict[str, Any] | None = None


class ReembedRequest(BaseModel):
    persist_dir: str | None = None
    backend: str | None = None


@app.get("/rag/stats")
async def rag_stats() -> Dict[str, Any]:
    base = "/workspace/data/vectorstore"
    import os, glob
    stats: Dict[str, Any] = {
        "meta_lines": 0,
        "texts_jsonl": 0,
        "faiss_index": False,
        "annoy_index": False,
    }
    try:
        meta = os.path.join(base, "meta.jsonl")
        if os.path.exists(meta):
            with open(meta, "r", encoding="utf-8") as f:
                for _ in f:
                    stats["meta_lines"] += 1
    except Exception:
        pass
    for path in glob.glob(os.path.join(base, "texts.jsonl")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for _ in f:
                    stats["texts_jsonl"] += 1
        except Exception:
            pass
    stats["faiss_index"] = os.path.exists(os.path.join(base, "index.faiss"))
    stats["annoy_index"] = os.path.exists(os.path.join(base, "index.ann"))
    return stats

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
    if REQ_COUNT is not None and REQ_LATENCY is not None:
        REQ_COUNT.labels(endpoint="handle").inc()  # type: ignore
        with REQ_LATENCY.labels(endpoint="handle").time():  # type: ignore
            resp = _kernel.handle(req.command, req.context or {})
    else:
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


@app.post("/rag/delete_source")
async def rag_delete_source(authorization: str | None = Header(default=None), source: str = Form(...)) -> Dict[str, Any]:
    if _api_token and authorization != f"Bearer {_api_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    cfg = load_yaml("/workspace/configs/vectorstore.yaml")
    persist_dir = cfg.get("persist_dir", "/workspace/data/vectorstore")
    backend = (cfg.get("backend", "memory")).lower()
    agent = ResearchAgent(persist_dir=persist_dir, backend=backend)
    try:
        res = agent.execute(f"delete source {source}", {})
        if getattr(agent, "_persist_dir", None):
            try:
                agent.index.save(agent._persist_dir)  # type: ignore[attr-defined]
            except Exception:
                pass
        return res
    except Exception:
        raise HTTPException(status_code=500, detail="delete_source_failed")


@app.post("/rag/upload")
async def rag_upload(authorization: str | None = Header(default=None), files: list[UploadFile] = File(...)) -> Dict[str, Any]:
    if _api_token and authorization != f"Bearer {_api_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Basic validation: max 50MB total, allowed extensions
    allowed_ext = {".pdf", ".txt", ".md"}
    total_bytes = 0
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
            name = uf.filename or "upload.bin"
            ext = os.path.splitext(name)[1].lower()
            if ext not in allowed_ext:
                continue
            if total_bytes > 50 * 1024 * 1024:
                break
            data = await uf.read()
            total_bytes += len(data)
            if total_bytes > 50 * 1024 * 1024:
                break
            dest = os.path.join(uploads_dir, name)
            with open(dest, "wb") as f:
                f.write(data)
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
        # Allow only http/https and cap size
        if not (url.startswith("http://") or url.startswith("https://")):
            raise HTTPException(status_code=400, detail="invalid_url")
        resp = requests.get(url, timeout=10, headers={"User-Agent": "JarvisCore/1.0"})
        if resp.status_code >= 400:
            raise HTTPException(status_code=400, detail="fetch_failed")
        if len(resp.text) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="content_too_large")
        # Write to a temp file and ingest
        uploads_dir = "/workspace/data/uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        import hashlib
        h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
        fname = os.path.join(uploads_dir, f"web_{h}.txt")
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


@app.post("/rag/crawl")
async def rag_crawl(authorization: str | None = Header(default=None), seed: str = Form(...), depth: int = Form(default=1)) -> Dict[str, Any]:
    if _api_token and authorization != f"Bearer {_api_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        from bs4 import BeautifulSoup  # type: ignore
        import requests  # type: ignore
        from urllib.parse import urljoin, urlparse
    except Exception:
        raise HTTPException(status_code=500, detail="crawler_deps_missing")
    seen: set[str] = set()
    to_visit: list[tuple[str,int]] = [(seed, 0)]
    uploads_dir = "/workspace/data/uploads"
    os.makedirs(uploads_dir, exist_ok=True)
    saved: list[str] = []
    while to_visit:
        url, d = to_visit.pop(0)
        if url in seen or d > depth:
            continue
        seen.add(url)
        try:
            resp = requests.get(url, timeout=10, headers={"User-Agent": "JarvisCoreCrawler/1.0"})
            if resp.status_code >= 400:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            # Save page
            import hashlib
            h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
            path = os.path.join(uploads_dir, f"crawl_{h}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(soup.get_text(" "))
            saved.append(path)
            # Enqueue links same host
            base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            for a in soup.find_all("a"):
                href = a.get("href")
                if not href:
                    continue
                nxt = urljoin(url, href)
                if urlparse(nxt).netloc == urlparse(base).netloc:
                    to_visit.append((nxt, d+1))
        except Exception:
            continue
    # Ingest saved
    cfg = load_yaml("/workspace/configs/vectorstore.yaml")
    persist_dir = cfg.get("persist_dir", "/workspace/data/vectorstore")
    backend = (cfg.get("backend", "memory")).lower()
    agent = ResearchAgent(persist_dir=persist_dir, backend=backend)
    for p in saved:
        try:
            agent.execute(f"ingest {p}", {})
        except Exception:
            continue
    try:
        if getattr(agent, "_persist_dir", None):
            agent.index.save(agent._persist_dir)  # type: ignore[attr-defined]
    except Exception:
        pass
    return {"status": "ok", "result": f"crawled_saved={len(saved)}", "artifacts": [{"type": "crawl", "items": saved}]}


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
# ------------------------ Defense Dashboard ------------------------

defense_summary__duplicate_definition_guard = True


@app.get("/defense/summary")
async def defense_summary() -> Dict[str, Any]:
    base = "/workspace/data/logs/security"
    counts: Dict[str, int] = {"suricata": 0, "zeek": 0, "wazuh": 0}
    severities: Dict[str, int] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    import glob, json
    alerts: list[Dict[str, Any]] = []
    for path in glob.glob(f"{base}/suricata_*.ndjson") + [f"{base}/suricata_manual.ndjson"]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                for ln in f:
                    try:
                        rec = json.loads(ln)
                        alerts.append(rec)
                        counts["suricata"] += 1
                        sev_val = str(rec.get("alert", {}).get("severity", "low")).lower()
                        # Map numeric severities (0-4) to bands
                        band = "low"
                        if sev_val in {"4", "critical"}: band = "critical"
                        elif sev_val in {"3", "high"}: band = "high"
                        elif sev_val in {"2", "medium"}: band = "medium"
                        else: band = "low"
                        severities[band] += 1
                    except Exception:
                        continue
        except Exception:
            pass
    for path in glob.glob(f"{base}/zeek_*.log"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for _ in f:
                    counts["zeek"] += 1
        except Exception:
            pass
    for path in glob.glob(f"{base}/wazuh_*.ndjson"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for _ in f:
                    counts["wazuh"] += 1
        except Exception:
            pass
    risk = score_events([{ "severity": sev } for sev, n in severities.items() for _ in range(n)])
    return {"counts": counts, "severities": severities, "risk": round(risk, 2)}


@app.get("/defense/stream")
async def defense_stream() -> Response:
    # Server-Sent Events (SSE) stream of new Suricata/Wazuh lines (best-effort)
    base = "/workspace/data/logs/security"
    import glob, json, aiofiles  # type: ignore

    async def _gen():  # type: ignore
        positions: Dict[str, int] = {}
        while True:
            files = set(glob.glob(f"{base}/suricata_*.ndjson")) | {f"{base}/suricata_manual.ndjson"}
            files |= set(glob.glob(f"{base}/wazuh_*.ndjson"))
            for path in files:
                try:
                    # initialize position
                    if path not in positions:
                        positions[path] = 0
                    # read new content
                    async with aiofiles.open(path, "r") as f:  # type: ignore
                        await f.seek(positions[path])
                        async for line in f:
                            positions[path] += len(line.encode("utf-8"))
                            data = line.strip()
                            if not data:
                                continue
                            # Validate JSON-ish; if invalid, wrap raw
                            try:
                                _ = json.loads(data)
                                payload = data
                            except Exception:
                                payload = json.dumps({"raw": data})
                            yield ("data: " + payload + "\n\n").encode("utf-8")
                except Exception:
                    continue
            await asyncio.sleep(1)

    return Response(content=_gen(), media_type="text/event-stream")


@app.get("/metrics")
async def metrics() -> Response:
    if generate_latest is None:
        return Response(content=b"metrics_not_enabled", media_type="text/plain")
    data = generate_latest()  # type: ignore
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)  # type: ignore


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
  <h3>Defense Summary</h3>
  <button id='refreshDefense'>Refresh</button>
  <pre id='defenseOut'></pre>
</div>
<div class='row'>
  <h3>RAG Stats</h3>
  <button id='refreshRag'>Refresh</button>
  <pre id='ragOut'></pre>
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
<div class='row'>
  <h3>Defense Dashboard</h3>
  <button id='refreshDefense'>Refresh Summary</button>
  <pre id='defenseOut'></pre>
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

// Defense summary
const refreshDefense = document.getElementById('refreshDefense');
refreshDefense.addEventListener('click', async () => {
  const resp = await fetch('/defense/summary');
  const data = await resp.json();
  document.getElementById('defenseOut').textContent = JSON.stringify(data, null, 2);
});

// RAG stats
const refreshRag = document.getElementById('refreshRag');
refreshRag.addEventListener('click', async () => {
  const resp = await fetch('/rag/stats');
  const data = await resp.json();
  document.getElementById('ragOut').textContent = JSON.stringify(data, null, 2);
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
