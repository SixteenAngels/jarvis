from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List

from .base import BaseAgent
from ..engineering.tools.spice_interface import simulate_circuit_stub
from ..engineering.tools.ngspice_cli import run_ngspice
from ..engineering.tools.kicad_cli import run_kicad_drc
from pathlib import Path


@dataclass
class LedDividerRequest:
    supply_v: float
    led_vf: float
    led_current_ma: float


def compute_series_resistor(supply_v: float, vf: float, current_ma: float) -> float:
    current_a = max(current_ma, 0.001) / 1000.0
    return max((supply_v - vf) / current_a, 0.0)


class ElectricalAgent(BaseAgent):
    name: str = "electrical"
    intents: List[str] = [
        "ohm",
        "resistor",
        "led",
        "divider",
        "pcb",
        "schematic",
        "electrical",
    ]

    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        lower = task.lower().strip()
        if lower.startswith("led resistor"):
            # format: "led resistor Vs=<v> Vf=<v> I=<mA>"
            params = self._parse_params(lower.replace("led resistor", "").strip())
            vs = float(params.get("vs", params.get("v", 5.0)))
            vf = float(params.get("vf", 2.0))
            cur = float(params.get("i", 10.0))
            r = compute_series_resistor(vs, vf, cur)
            return {"status": "ok", "result": f"R ≈ {r:.1f} Ω (Vs={vs}V, Vf={vf}V, I={cur}mA)", "artifacts": []}

        if lower.startswith("ohm"):
            # format: "ohm V=<volts> I=<amps>" -> R
            params = self._parse_params(lower.replace("ohm", "").strip())
            v = float(params.get("v", 5.0))
            i = float(params.get("i", 0.01))
            r = v / max(i, 1e-9)
            return {"status": "ok", "result": f"R ≈ {r:.2f} Ω (V={v}V, I={i}A)", "artifacts": []}

        if lower.startswith("simulate "):
            # simulate <netlist_path>
            netlist = task.split(" ", 1)[1].strip()
            out = run_ngspice(netlist)
            return out

        if lower.startswith("drc ") or lower.startswith("kicad drc "):
            # drc <board.kicad_pcb>
            board = task.split(" ", 1)[1].strip() if lower.startswith("drc ") else task.split(" ", 2)[2].strip()
            res = run_kicad_drc(board)
            # persist result as artifact for traceability
            try:
                artifacts_dir = Path("/workspace/data/artifacts/drc")
                artifacts_dir.mkdir(parents=True, exist_ok=True)
                board_name = Path(board).stem or "board"
                out_path = artifacts_dir / f"{board_name}_drc.txt"
                (out_path).write_text(res.get("result", ""), encoding="utf-8")
                res.setdefault("artifacts", []).append({"type": "drc", "path": str(out_path)})
            except Exception:
                pass
            return res

        return {"status": "error", "result": "Unknown electrical command", "artifacts": []}

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
