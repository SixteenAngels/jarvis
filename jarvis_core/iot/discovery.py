from __future__ import annotations

"""MQTT/ROS2 device discovery helpers.

This module provides basic discovery utilities to enumerate devices/topics on
an MQTT broker and ROS bridge. These are lightweight, best-effort probes to
bootstrap dashboards and routing tables.
"""

from typing import Dict, Any, List
import time

try:
    import paho.mqtt.client as mqtt  # type: ignore
except Exception:  # pragma: no cover
    mqtt = None  # type: ignore

try:
    import roslibpy  # type: ignore
except Exception:  # pragma: no cover
    roslibpy = None  # type: ignore


def discover_mqtt(broker: str = "localhost", timeout_s: int = 3) -> Dict[str, Any]:
    """Return a basic snapshot of MQTT topics by subscribing to wildcard.

    Uses retained messages to gather a minimal view without active publishing.
    """
    if mqtt is None:
        return {"enabled": False, "topics": []}
    topics: List[str] = []

    def on_message(_c, _u, msg):
        t = msg.topic
        if t not in topics:
            topics.append(t)

    client = mqtt.Client()
    client.on_message = on_message
    try:
        client.connect(broker)
        client.subscribe("#")
        client.loop_start()
        time.sleep(timeout_s)
    finally:
        try:
            client.loop_stop()
            client.disconnect()
        except Exception:
            pass
    return {"enabled": True, "topics": sorted(topics)}


def discover_ros(host: str = "localhost", port: int = 9090, timeout_s: int = 3) -> Dict[str, Any]:
    """Return lists of topics and services from a ROS bridge, if available."""
    if roslibpy is None:
        return {"enabled": False, "topics": [], "services": []}
    client = roslibpy.Ros(host=host, port=port)
    try:
        client.run()
        topics = client.get_topics() or []
        services = client.get_services() or []
        return {"enabled": True, "topics": topics, "services": services}
    except Exception:
        return {"enabled": False, "topics": [], "services": []}
    finally:
        try:
            client.terminate()
        except Exception:
            pass
