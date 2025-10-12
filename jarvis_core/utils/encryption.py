from __future__ import annotations

from typing import Tuple

try:
    from cryptography.fernet import Fernet  # type: ignore
except Exception:  # pragma: no cover - optional
    Fernet = None  # type: ignore


def generate_key() -> bytes:
    if Fernet:
        return Fernet.generate_key()
    # fallback: not secure, for testing only
    import os
    return os.urandom(32)


def encrypt(data: bytes, key: bytes) -> bytes:
    if Fernet:
        return Fernet(key).encrypt(data)
    return data[::-1]


def decrypt(token: bytes, key: bytes) -> bytes:
    if Fernet:
        return Fernet(key).decrypt(token)
    return token[::-1]
