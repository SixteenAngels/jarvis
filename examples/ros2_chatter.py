"""
Example: ROS2 chatter via roslibpy (ROS bridge).

Usage:
  python examples/ros2_chatter.py --host localhost --port 9090
"""
from __future__ import annotations

import argparse
from jarvis_core.robotics.ros2_node import publish_example


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=9090)
    args = parser.parse_args()

    ok = publish_example(args.host, args.port)
    print("Published" if ok else "ROS bridge not available")


if __name__ == "__main__":
    main()
