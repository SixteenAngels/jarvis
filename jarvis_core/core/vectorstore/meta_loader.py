from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Iterable, List


def read_meta_lines(path: str | Path) -> Iterable[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    def _iter():
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    return list(_iter())


essential_keys = ("source",)


def normalize(record: Dict[str, Any]) -> Dict[str, Any]:
    rec = dict(record)
    for k in essential_keys:
        rec.setdefault(k, "unknown")
    return rec


def group_by_source(records: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        rec = normalize(r)
        src = rec.get("source", "unknown")
        buckets.setdefault(src, []).append(rec)
    return buckets


def unique_sources(records: Iterable[Dict[str, Any]]) -> List[str]:
    return sorted(set(normalize(r).get("source", "unknown") for r in records))
