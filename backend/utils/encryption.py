import os
import base64
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SECRET = base64.b64decode(os.environ.get("AI_KEY_ENCRYPTION_SECRET", "A" * 44))  # 32 bytes


def encrypt_api_key(plaintext: str) -> str:
    nonce = secrets.token_bytes(12)
    ct = AESGCM(SECRET).encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ct).decode()


def decrypt_api_key(ciphertext: str) -> str:
    raw = base64.b64decode(ciphertext)
    nonce, ct = raw[:12], raw[12:]
    return AESGCM(SECRET).decrypt(nonce, ct, None).decode()
