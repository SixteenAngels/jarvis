from __future__ import annotations

from pathlib import Path

def simulate_circuit_stub(netlist_path: str) -> str:
    # Very simple: check file and return a pretend result
    p = Path(netlist_path)
    if not p.exists():
        return "error: netlist not found"
    return "ok: transient analysis stable"
