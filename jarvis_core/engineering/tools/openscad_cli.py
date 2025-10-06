from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any

from .freecad_interface import generate_cad_stub


def run_openscad(scad_src: str, output_path: str | None = None) -> Dict[str, Any]:
    exe = shutil.which("openscad")
    if not exe:
        path = generate_cad_stub(Path(output_path).parent.as_posix() if output_path else "/workspace/data/artifacts/cad")
        return {"status": "ok", "result": f"[stub] CAD at {path}", "artifacts": [{"type": "cad", "path": path}]}
    src = Path(scad_src)
    if not src.exists():
        return {"status": "error", "result": "scad not found", "artifacts": []}
    out = Path(output_path) if output_path else src.with_suffix(".stl")
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run([exe, "-o", str(out), str(src)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
        status = "ok" if proc.returncode == 0 else "error"
        return {"status": status, "result": proc.stdout or proc.stderr, "artifacts": [{"type": "cad", "path": str(out)}]}
    except Exception as e:
        path = generate_cad_stub(out.parent.as_posix())
        return {"status": "ok", "result": f"[fallback] CAD at {path} ({e})", "artifacts": [{"type": "cad", "path": path}]}
