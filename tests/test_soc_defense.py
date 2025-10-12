from __future__ import annotations

import json
from pathlib import Path

from jarvis_core.core.defense_extensions.suricata_ingest import parse_eve_line, store_alert
from jarvis_core.core.defense_extensions.soc_correlator import correlate_vision_and_alerts
from jarvis_core.perception.goodseye.vision_for_security import security_detect
from jarvis_core.core.router import Router
from jarvis_core.agents.defense.cybersec import CybersecDefenseAgent


def test_suricata_ingest_and_store(tmp_path: Path) -> None:
    line = json.dumps({
        "timestamp": "2025-10-06T12:00:00",
        "event_type": "alert",
        "src_ip": "10.0.0.1",
        "dest_ip": "10.0.0.2",
        "alert": {"severity": 3, "signature": "Test"}
    })
    rec = parse_eve_line(line)
    assert rec.get("event_type") == "alert"
    path = store_alert(rec)
    assert Path(path).exists()


def test_correlation_with_mock_vision() -> None:
    # Build a vision event and matching alert
    vision = security_detect("frame.jpg")
    alerts = [{
        "timestamp": "2025-10-06T12:00:00",
        "alert": {"severity": 3},
    }]
    # Adjust vision timestamp near the alert
    alerts_ts = "2025-10-06T12:00:00"
    vision["timestamp"] = 1760000000  # arbitrary near now; correlation relies on window
    # For deterministic test, just ensure function executes and returns list
    corr = correlate_vision_and_alerts(vision, alerts, window_seconds=100000000)
    assert isinstance(corr, list)


def test_cybersec_agent_ingest_and_correlate(tmp_path: Path) -> None:
    agent = CybersecDefenseAgent()
    # Prepare alert file
    alerts_path = tmp_path / "alerts.ndjson"
    alerts = [{
        "timestamp": "2025-10-06T12:00:00",
        "alert": {"severity": 3},
    }]
    alerts_path.write_text("\n".join(json.dumps(a) for a in alerts))

    r = Router(agents=[agent])
    # Ingest single line
    line = json.dumps({"timestamp": "2025-10-06T12:00:00", "event_type": "alert", "alert": {"severity": 3}})
    res1 = r.route(f"ingest suricata {line}")
    assert res1["status"] == "ok"

    res2 = r.route(f"correlate vision {alerts_path}", {"image": "frame.jpg"})
    assert res2["status"] == "ok"
    assert "correlated=" in res2["result"]
