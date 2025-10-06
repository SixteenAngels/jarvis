from __future__ import annotations

from typing import Dict, Any


class LocalLLMAdapter:
    def __init__(self) -> None:
        pass

    def generate(self, prompt: str, params: Dict[str, Any] | None = None) -> str:
        # Very naive placeholder: echoes the prompt with a trivial transform
        params = params or {}
        return f"[local-llm] {prompt.strip()}"
