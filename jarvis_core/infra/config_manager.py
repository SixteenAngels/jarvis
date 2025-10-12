from __future__ import annotations

from typing import Dict, Any
from pathlib import Path

from ..utils.config import load_yaml


def load_profiles(base: str, overrides: Dict[str, str] | None = None) -> Dict[str, Any]:
    cfg: Dict[str, Any] = {}
    basep = Path(base)
    if basep.exists():
        for p in sorted(basep.glob("*.yaml")):
            cfg |= load_yaml(p)
    for _, path in (overrides or {}).items():
        cfg |= load_yaml(path)
    return cfg
}