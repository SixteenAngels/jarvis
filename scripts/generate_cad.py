#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from jarvis_core.engineering.tools.freecad_interface import generate_cad_stub

def main() -> int:
    outdir = sys.argv[1] if len(sys.argv) > 1 else "/workspace/data/artifacts/cad"
    path = generate_cad_stub(outdir)
    print(f"CAD generated at {path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
