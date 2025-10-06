from __future__ import annotations

from pathlib import Path

def generate_cad_stub(output_dir: str) -> str:
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    out = p / "model.stl"
    out.write_text("solid mock\nendsolid\n")
    return str(out)
