from __future__ import annotations

from typing import List, Dict, Any, Optional

from ..agents.base import BaseAgent
from ..agents.research import ResearchAgent
from ..agents.system import SystemAgent
from ..agents.comms import CommsAgent
from ..agents.biomedical import BiomedicalAgent
from ..agents.electrical import ElectricalAgent
from ..agents.mechanical import MechanicalAgent
from ..agents.software import SoftwareAgent
from ..agents.defense_agent import DefenseAgent
from ..agents.robotics import RoboticsAgent
from ..agents.civil import CivilAgent
from ..agents.defense.cybersec import CybersecDefenseAgent
from ..agents.engineering.software import ComputerEngineerAgent


class Router:
    """Simple router that picks the first agent that can handle a task.

    Future: add embedding similarity and reflection feedback.
    """

    def __init__(self, agents: Optional[List[BaseAgent]] = None) -> None:
        # Default registry includes research, system, comms, biomedical, electrical, mechanical, software, defense, robotics, civil, cybersec_defense, computer_engineer
        self.agents: List[BaseAgent] = agents or [
            ResearchAgent(),
            SystemAgent(),
            CommsAgent(),
            BiomedicalAgent(),
            ElectricalAgent(),
            MechanicalAgent(),
            SoftwareAgent(),
            DefenseAgent(),
            RoboticsAgent(),
            CivilAgent(),
            CybersecDefenseAgent(),
            ComputerEngineerAgent(),
        ]
        self._corrections_path = "/workspace/data/router_corrections.json"
        self._weights_path = "/workspace/data/router_weights.json"
        self._weights: Dict[str, float] = self._load_weights()
        # Apply a small decay on startup to avoid ever-growing bias
        self._decay_weights(0.99)
        self._save_weights()

    def record_correction(self, task: str, corrected_agent: str) -> None:
        import json, os
        os.makedirs("/workspace/data", exist_ok=True)
        try:
            data: List[Dict[str, Any]] = []
            try:
                with open(self._corrections_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = []
            data.append({"task": task, "agent": corrected_agent})
            with open(self._corrections_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass
        # Update learned weights and persist
        try:
            name = corrected_agent
            self._weights[name] = self._weights.get(name, 0.0) + 0.1
            self._save_weights()
        except Exception:
            pass

    def _load_weights(self) -> Dict[str, float]:
        """Load simple per-agent weights from corrections history.

        Agents that were used as corrections receive a small positive weight,
        biasing selection when multiple agents can_handle().
        """
        import json, os
        # Prefer direct weights file if available
        try:
            if os.path.exists(self._weights_path):
                with open(self._weights_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        # Fallback: compute from corrections history
        try:
            with open(self._corrections_path, "r", encoding="utf-8") as f:
                rows = json.load(f)
        except Exception:
            rows = []
        weights: Dict[str, float] = {}
        for row in rows:
            agent = row.get("agent")
            if agent:
                weights[agent] = weights.get(agent, 0.0) + 0.1
        return weights

    def _save_weights(self) -> None:
        import json, os
        try:
            os.makedirs("/workspace/data", exist_ok=True)
            with open(self._weights_path, "w", encoding="utf-8") as f:
                json.dump(self._weights, f)
        except Exception:
            pass

    def _decay_weights(self, factor: float = 0.99) -> None:
        if not self._weights:
            return
        for k in list(self._weights.keys()):
            self._weights[k] *= factor
            if abs(self._weights[k]) < 1e-6:
                del self._weights[k]

    def register(self, agent: BaseAgent) -> None:
        self.agents.append(agent)

    def route(self, task: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        context = context or {}
        # Prefer agents with a positive learned weight when multiple match
        candidates: List[BaseAgent] = [a for a in self.agents if a.can_handle(task)]
        if candidates:
            candidates.sort(key=lambda a: self._weights.get(getattr(a, "name", a.__class__.__name__), 0.0), reverse=True)
            return candidates[0].execute(task, context)
        for agent in self.agents:
            if agent.can_handle(task):
                return agent.execute(task, context)
        # fallback: try all, pick best non-empty response
        best: Dict[str, Any] | None = None
        for agent in self.agents:
            resp = agent.execute(task, context)
            if resp.get("status") == "ok" and resp.get("result"):
                best = resp
                break
        return best or {"status": "error", "result": "No agent could handle the task", "artifacts": []}
