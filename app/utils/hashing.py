import hashlib


def sha256_bytes(content: bytes) -> str:
    """Return the SHA256 hex digest for raw bytes."""
    return hashlib.sha256(content).hexdigest()
