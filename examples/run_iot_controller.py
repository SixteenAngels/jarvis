"""
Example: IoT control stubs via IoT agents.

Usage:
  python examples/run_iot_controller.py
"""
from __future__ import annotations

from jarvis_core.core.router import Router
from jarvis_core.agents.iot.home_assistant import HomeAssistantAgent
from jarvis_core.agents.iot.device_control import DeviceControlAgent


def main() -> None:
    r = Router(agents=[HomeAssistantAgent(), DeviceControlAgent()])
    print(r.route("device control toggle light", {}))


if __name__ == "__main__":
    main()
