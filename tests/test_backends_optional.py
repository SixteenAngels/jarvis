from __future__ import annotations

import pytest

from jarvis_core.core.vectorstore.factory import get_index


def test_get_index_memory() -> None:
    idx = get_index("memory")
    assert hasattr(idx, "add_texts") and hasattr(idx, "search")


def test_get_index_faiss_optional() -> None:
    try:
        idx = get_index("faiss")
    except Exception as e:
        pytest.fail(f"Factory should not raise: {e}")


def test_get_index_annoy_optional() -> None:
    try:
        idx = get_index("annoy")
    except Exception as e:
        pytest.fail(f"Factory should not raise: {e}")
