from __future__ import annotations

import json
from typing import Callable

try:
    import paho.mqtt.client as mqtt  # type: ignore
except Exception:  # pragma: no cover
    mqtt = None  # type: ignore


def connect_and_subscribe(broker: str, topic: str, on_message: Callable[[str, str], None]) -> None:
    if mqtt is None:
        return
    client = mqtt.Client()
    client.on_message = lambda _c, _u, msg: on_message(msg.topic, msg.payload.decode("utf-8", errors="ignore"))
    client.connect(broker)
    client.subscribe(topic)
    client.loop_start()
