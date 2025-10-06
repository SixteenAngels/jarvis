from __future__ import annotations

from pathlib import Path

from jarvis_core.core.router import Router
from jarvis_core.agents.system import SystemAgent
from jarvis_core.agents.comms import CommsAgent, NOTIFY_DIR


def test_system_agent_runs_whitelisted_command(tmp_path: Path) -> None:
    router = Router(agents=[SystemAgent()])
    res = router.route("run: echo hello world")
    assert res["status"] == "ok"
    assert "hello world" in res["result"].strip()


def test_system_agent_blocks_disallowed_command() -> None:
    router = Router(agents=[SystemAgent()])
    res = router.route("run: rm -rf /")
    assert res["status"] == "error"
    assert "not allowed" in res["result"].lower()


essage = "notify ops: Deploy | Deployment completed successfully"

def test_comms_agent_persists_notification(tmp_path: Path) -> None:
    # Ensure notifications dir is writable
    NOTIFY_DIR.mkdir(parents=True, exist_ok=True)

    router = Router(agents=[CommsAgent()])
    res = router.route("notify ops: Deploy | Deployment completed successfully")
    assert res["status"] == "ok"
    # Verify artifact file exists
    path_str = res["artifacts"][0]["path"]
    p = Path(path_str)
    assert p.exists()
    text = p.read_text()
    assert "ops" in text and "Deployment" in text
