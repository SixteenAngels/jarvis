from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Any


class BaseAgent(ABC):
    """Abstract base class for all agents.

    Each agent declares a name and intents (keywords/phrases) that describe
    the type of tasks it is designed to handle.
    """

    name: str = "base"
    intents: List[str] = []

    def __init__(self) -> None:
        pass

    def can_handle(self, task: str) -> bool:
        """Return True if this agent can handle the given task string.

        Default implementation: simple keyword match against lowercased task.
        Agents may override for more advanced logic.
        """
        if not task:
            return False
        lower_task = task.lower()
        return any(intent.lower() in lower_task for intent in self.intents)

    @abstractmethod
    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the task and return a structured response.

        Returns a dict like:
            {
                "status": "ok" | "error",
                "result": str,
                "artifacts": List[Dict[str, Any]]
            }
        """
        raise NotImplementedError
