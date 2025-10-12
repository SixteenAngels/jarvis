from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml


def load_yaml(path: str | Path | None) -> Dict[str, Any]:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    try:
        raw = p.read_text(encoding="utf-8")
        # simple ${ENV_VAR} substitution
        def replace_env(match):
            var = match.group(1)
            return os.getenv(var, "")
        import re
        raw = re.sub(r"\$\{([^}]+)\}", replace_env, raw)
        data = yaml.safe_load(raw) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}
