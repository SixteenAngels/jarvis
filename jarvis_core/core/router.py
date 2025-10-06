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
from ..agents.defense import DefenseAgent
from ..agents.robotics import RoboticsAgent
from ..agents.civil import CivilAgent


class Router:
    """Simple router that picks the first agent that can handle a task.

    Future: add embedding similarity and reflection feedback.
    """

    def __init__(self, agents: Optional[List[BaseAgent]] = None) -> None:
        # Default registry includes research, system, comms, biomedical, electrical, mechanical, software, defense, robotics, civil
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
        ]

    def register(self, agent: BaseAgent) -> None:
        self.agents.append(agent)

    def route(self, task: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        context = context or {}
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
