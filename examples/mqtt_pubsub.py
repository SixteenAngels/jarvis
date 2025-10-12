"""
Example: MQTT publish/subscribe using the IoT client skeleton.

Usage:
  python examples/mqtt_pubsub.py --broker localhost --topic demo/test
"""
from __future__ import annotations

import argparse
import time
from jarvis_core.iot.mqtt_client import connect_and_subscribe


def on_message(topic: str, payload: str) -> None:
    print(f"[MQTT] {topic}: {payload}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--broker", default="localhost")
    parser.add_argument("--topic", default="demo/test")
    args = parser.parse_args()

    connect_and_subscribe(args.broker, args.topic, on_message)
    print("Subscribed; press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()
