from __future__ import annotations

import os
from typing import Dict, Any


class GPT5Adapter:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def available(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, params: Dict[str, Any] | None = None) -> str:
        # Placeholder without making external calls in tests
        return f"[gpt5] {prompt.strip()}"
