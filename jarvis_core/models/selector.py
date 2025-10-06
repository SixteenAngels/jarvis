from __future__ import annotations

from typing import Dict, Any

from .gpt5_adapter import GPT5Adapter
from .local_llm_adapter import LocalLLMAdapter


class ModelSelector:
    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.cloud = GPT5Adapter()
        self.local = LocalLLMAdapter()
        self.failure_count = 0
        self.backoff_until = 0

    def generate(self, prompt: str, params: Dict[str, Any] | None = None) -> str:
        import time
        now = time.time()
        # Simple backoff if failures occurred
        if self.failure_count > 0 and now < self.backoff_until:
            return self.local.generate(prompt, params)
        try:
            if self.cloud.available():
                return self.cloud.generate(prompt, params)
        except Exception:
            self.failure_count += 1
            self.backoff_until = now + min(60, 2 ** self.failure_count)
        return self.local.generate(prompt, params)
