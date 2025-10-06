from __future__ import annotations

from collections import deque
from typing import Deque, List


class ShortTermMemory:
    def __init__(self, max_items: int = 50) -> None:
        self.buffer: Deque[str] = deque(maxlen=max_items)

    def add(self, item: str) -> None:
        self.buffer.append(item)

    def get(self, n: int = 10) -> List[str]:
        return list(self.buffer)[-n:]
