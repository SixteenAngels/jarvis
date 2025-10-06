from __future__ import annotations

from typing import Dict, Any

from .gpt5_adapter import GPT5Adapter
from .local_llm_adapter import LocalLLMAdapter


class ModelSelector:
    def __init__(self) -> None:
        self.cloud = GPT5Adapter()
        self.local = LocalLLMAdapter()

    def generate(self, prompt: str, params: Dict[str, Any] | None = None) -> str:
        if self.cloud.available():
            return self.cloud.generate(prompt, params)
        return self.local.generate(prompt, params)
