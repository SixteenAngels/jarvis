from __future__ import annotations

import hmac
import hashlib
from typing import Tuple

try:
    from cryptography.hazmat.primitives.asymmetric import rsa, padding  # type: ignore
    from cryptography.hazmat.primitives import hashes, serialization  # type: ignore
    CRYPTO_AVAILABLE = True
except Exception:  # pragma: no cover - optional
    CRYPTO_AVAILABLE = False


def sign_hmac(data: bytes, key: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha256).digest()


def verify_hmac(data: bytes, key: bytes, signature: bytes) -> bool:
    expected = sign_hmac(data, key)
    return hmac.compare_digest(expected, signature)


def generate_rsa_keypair() -> Tuple[bytes, bytes]:
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography not available")
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv_pem, pub_pem


def sign_rsa(data: bytes, private_pem: bytes) -> bytes:
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography not available")
    private_key = serialization.load_pem_private_key(private_pem, password=None)
    return private_key.sign(
        data,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256(),
    )


def verify_rsa(data: bytes, signature: bytes, public_pem: bytes) -> bool:
    if not CRYPTO_AVAILABLE:
        return False
    from cryptography.exceptions import InvalidSignature  # type: ignore

    public_key = serialization.load_pem_public_key(public_pem)
    try:
        public_key.verify(
            signature,
            data,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
        return True
    except InvalidSignature:
        return False
