#!/usr/bin/env python3
"""
Jarvis Core — main entrypoint.

Run in CLI mode (default) or start the FastAPI server.

Examples:
  - CLI (single command):
      python main.py "query alpha beta"
  - CLI (interactive):
      python main.py
      > ingest /path/to/docs
      > query alpha
  - API server:
      python main.py --api --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import argparse
import sys
from typing import Dict, Any

from jarvis_core.core.kernel import Kernel


def run_cli(args: argparse.Namespace) -> int:
    """Run Kernel in CLI mode.

    If a command is provided, execute it once. Otherwise, start a simple REPL
    until EOF/KeyboardInterrupt.
    """
    kernel = Kernel()
    if args.command:
        resp = kernel.handle(" ".join(args.command))
        print(resp)
        return 0

    # Interactive loop
    print("Jarvis Core CLI. Type commands; Ctrl+C to exit.")
    try:
        while True:
            line = input("> ").strip()
            if not line:
                continue
            resp = kernel.handle(line)
            print(resp)
    except (EOFError, KeyboardInterrupt):
        print()
        return 0


def run_api(args: argparse.Namespace) -> int:
    """Start the FastAPI server via uvicorn.

    Requires uvicorn to be installed (available in full requirements profile).
    """
    try:
        import uvicorn  # type: ignore
    except Exception:
        print("uvicorn is not installed. Please install full requirements.")
        return 1
    uvicorn.run(
        "jarvis_core.core.http_api_fast:app",
        host=args.host,
        port=args.port,
        reload=False,
    )
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="jarvis-core")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run in CLI mode")
    parser.add_argument("--api", action="store_true", help="Run FastAPI server instead of CLI")
    parser.add_argument("--host", default="0.0.0.0", help="API host (when --api)")
    parser.add_argument("--port", type=int, default=8000, help="API port (when --api)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.api:
        return run_api(args)
    return run_cli(args)


if __name__ == "__main__":
    raise SystemExit(main())
