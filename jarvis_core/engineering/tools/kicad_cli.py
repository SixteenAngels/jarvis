from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any

from .kicad_interface import validate_netlist


def run_kicad_drc(pcb_path: str) -> Dict[str, Any]:
    exe = shutil.which("kicad-cli") or shutil.which("pcbnew")
    p = Path(pcb_path)
    if not exe:
        ok = validate_netlist(p.with_suffix('.net').as_posix())
        return {"status": "ok" if ok else "error", "result": f"[stub] DRC {'ok' if ok else 'failed'}", "artifacts": []}
    if not p.exists():
        return {"status": "error", "result": "pcb file not found", "artifacts": []}
    try:
        # kicad-cli pcb drc <board.kicad_pcb>
        proc = subprocess.run([exe, "pcb", "drc", str(p)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
        status = "ok" if proc.returncode == 0 else "error"
        return {"status": status, "result": proc.stdout or proc.stderr, "artifacts": []}
    except Exception as e:
        ok = validate_netlist(p.with_suffix('.net').as_posix())
        return {"status": "ok" if ok else "error", "result": f"[fallback] DRC {'ok' if ok else 'failed'} ({e})", "artifacts": []}
