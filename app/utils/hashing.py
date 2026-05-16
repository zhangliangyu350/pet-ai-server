import hashlib


def sha256_bytes(content: bytes) -> str:
    """返回原始字节的 SHA256 十六进制摘要。"""
    return hashlib.sha256(content).hexdigest()
