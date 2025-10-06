from __future__ import annotations

from typing import Dict, Any

from .gpt5_adapter import GPT5Adapter
from .local_llm_adapter import LocalLLMAdapter
from ..utils.config import load_yaml


class ModelSelector:
    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = load_yaml("/workspace/configs/models.yaml").get("selector", {}) | (config or {})
        self.cloud = GPT5Adapter()
        self.local = LocalLLMAdapter()
        self.failure_count = 0
        self.backoff_until = 0

    def generate(self, prompt: str, params: Dict[str, Any] | None = None) -> str:
        import time
        now = time.time()
        # Configurable backoff
        backoff_conf = int(self.config.get("backoff_seconds", 0))
        if backoff_conf:
            self.backoff_until = max(self.backoff_until, now + backoff_conf)
        if self.failure_count > 0 and now < self.backoff_until:
            return self.local.generate(prompt, params)
        prefer = (self.config.get("prefer") or "auto").lower()
        try:
            if prefer in ("cloud", "auto") and self.cloud.available():
                return self.cloud.generate(prompt, params)
        except Exception:
            self.failure_count += 1
            self.backoff_until = now + min(60, 2 ** self.failure_count)
        if prefer == "cloud":
            # if explicitly cloud but unavailable, fallback local anyway
            return self.local.generate(prompt, params)
        if prefer == "local":
            return self.local.generate(prompt, params)
        return self.local.generate(prompt, params)
