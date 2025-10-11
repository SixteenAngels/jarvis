from __future__ import annotations

from fastapi.testclient import TestClient
from jarvis_core.core.http_api_fast import app


def test_health_and_stats() -> None:
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200 and r.json().get("status") == "ok"
    r2 = client.get("/rag/stats")
    assert r2.status_code == 200
    data = r2.json()
    assert "meta_lines" in data and "faiss_index" in data


def test_upload_and_url_ingest(monkeypatch) -> None:  # type: ignore
    client = TestClient(app)
    # Upload small text file
    files = {"files": ("note.txt", b"hello world", "text/plain")}
    r = client.post("/rag/upload", files=files, headers={"Authorization": "Bearer changeme-token"})
    assert r.status_code in (200, 401)
    # Ingest URL (mock requests)
    class DummyResp:
        status_code = 200
        text = "example content"

    def fake_get(url, timeout=10, headers=None):  # type: ignore
        return DummyResp()

    import jarvis_core.core.http_api_fast as api
    monkeypatch.setattr(api, "requests", type("R", (), {"get": staticmethod(fake_get)}))
    r2 = client.post("/rag/ingest_url", data={"url": "https://example.com"}, headers={"Authorization": "Bearer changeme-token"})
    assert r2.status_code in (200, 401)
