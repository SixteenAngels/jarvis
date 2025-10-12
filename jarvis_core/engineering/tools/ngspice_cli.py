from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any

from .spice_interface import simulate_circuit_stub


def run_ngspice(netlist_path: str, workdir: str | None = None) -> Dict[str, Any]:
    """Run ngspice in batch mode if available; fallback to stub.

    Returns dict: {status, result, artifacts:[{type,path}?]}
    """
    exe = shutil.which("ngspice")
    if not exe:
        # fallback
        res = simulate_circuit_stub(netlist_path)
        return {"status": "ok" if res.startswith("ok") else "error", "result": f"[stub] {res}", "artifacts": []}
    p = Path(netlist_path)
    if not p.exists():
        return {"status": "error", "result": "netlist not found", "artifacts": []}
    try:
        proc = subprocess.run([exe, "-b", str(p)], cwd=workdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        status = "ok" if proc.returncode == 0 else "error"
        return {"status": status, "result": proc.stdout or proc.stderr, "artifacts": []}
    except Exception as e:
        res = simulate_circuit_stub(netlist_path)
        return {"status": "ok", "result": f"[fallback] {res} ({e})", "artifacts": []}
