from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List

from .base import BaseAgent
from ..engineering.tools.freecad_interface import generate_cad_stub


@dataclass
class Beam:
    youngs_modulus_pa: float  # E
    moment_of_inertia_m4: float  # I
    length_m: float  # L


def simply_supported_center_load_deflection(newton: float, beam: Beam) -> float:
    # delta = (F * L^3) / (48 * E * I)
    numerator = newton * (beam.length_m ** 3)
    denominator = 48.0 * beam.youngs_modulus_pa * beam.moment_of_inertia_m4
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def gear_ratio(driver_teeth: int, driven_teeth: int) -> float:
    return float(driven_teeth) / max(driver_teeth, 1)


class MechanicalAgent(BaseAgent):
    name: str = "mechanical"
    intents: List[str] = [
        "beam",
        "deflection",
        "gear",
        "ratio",
        "mechanical",
    ]

    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        lower = task.lower().strip()
        if lower.startswith("beam deflection"):
            # format: beam deflection F=<N> L=<m> E=<Pa> I=<m4>
            params = self._parse_params(lower.replace("beam deflection", "").strip())
            f = float(params.get("f", 100.0))
            L = float(params.get("l", 1.0))
            E = float(params.get("e", 2e11))
            I = float(params.get("i", 1e-6))
            d = simply_supported_center_load_deflection(f, Beam(E, I, L))
            return {"status": "ok", "result": f"δ ≈ {d:.6f} m (F={f}N, L={L}m)", "artifacts": []}

        if lower.startswith("gear ratio"):
            # format: gear ratio driver=<z1> driven=<z2>
            params = self._parse_params(lower.replace("gear ratio", "").strip())
            z1 = int(params.get("driver", 20))
            z2 = int(params.get("driven", 40))
            gr = gear_ratio(z1, z2)
            return {"status": "ok", "result": f"ratio ≈ {gr:.3f} (driven/driver)", "artifacts": []}

        if lower.startswith("generate cad"):
            # format: generate cad <outdir>
            parts = task.split(" ", 2)
            outdir = parts[2] if len(parts) > 2 else "/workspace/data/artifacts/cad"
            path = generate_cad_stub(outdir)
            return {"status": "ok", "result": f"cad at {path}", "artifacts": [{"type": "cad", "path": path}]}

        return {"status": "error", "result": "Unknown mechanical command", "artifacts": []}

    def _parse_params(self, s: str) -> Dict[str, float]:
        params: Dict[str, float] = {}
        for part in s.split():
            if "=" in part:
                k, v = part.split("=", 1)
                try:
                    params[k.strip()] = float(v)
                except Exception:
                    pass
        return params
