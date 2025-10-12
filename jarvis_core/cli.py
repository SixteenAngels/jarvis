from __future__ import annotations

import argparse

from .core.kernel import Kernel


def main() -> None:
    parser = argparse.ArgumentParser(prog="jarvis-core")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="User input to the Kernel")
    args = parser.parse_args()

    kernel = Kernel()
    user_input = " ".join(args.command).strip()
    if not user_input:
        print("Please provide a command.")
        return
    resp = kernel.handle(user_input)
    print(resp.get("status", ""))
    print(resp.get("result", ""))


if __name__ == "__main__":
    main()
