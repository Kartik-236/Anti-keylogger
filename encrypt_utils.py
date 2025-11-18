# encrypt_utils.py
import os
import binascii
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# Files (project root)
PASSFILE = "secret.pass"    # optional passphrase file (host-only, chmod 600)
HEXKEY = "secret.hex"       # optional legacy key (hex or raw bytes)
# Environment variable (session-only, safer)
ENV_PASS = "AK_PASS"

# PBKDF2 params (demo-appropriate; increase iterations for production)
_SALT = b"anti-keylogger-salt-v1"
_ITER = 200_000
_KEY_LEN = 32  # AES-256

def _derive_from_passphrase(passphrase: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=_KEY_LEN,
        salt=_SALT,
        iterations=_ITER,
        backend=default_backend()
    )
    return kdf.derive(passphrase)

def load_key() -> bytes:
    """
    Return a 32-byte AES key.
    Priority:
      1) AK_PASS env var (utf-8)
      2) secret.pass (raw utf-8 passphrase)
      3) secret.hex (hex string of 32 bytes OR raw 32 bytes)
    Raises FileNotFoundError or ValueError on failure.
    """
    # 1) env var
    val = os.environ.get(ENV_PASS)
    if val:
        if isinstance(val, str):
            val = val.encode("utf-8")
        return _derive_from_passphrase(val)

    # 2) pass file
    if os.path.exists(PASSFILE):
        with open(PASSFILE, "rb") as f:
            pf = f.read().strip()
            if not pf:
                raise ValueError("secret.pass is empty")
            return _derive_from_passphrase(pf)

    # 3) secret.hex
    if os.path.exists(HEXKEY):
        with open(HEXKEY, "rb") as f:
            raw = f.read().strip()
            if not raw:
                raise ValueError("secret.hex is empty")
            # try interpret as ascii hex string (64 hex chars -> 32 bytes)
            try:
                s = raw.decode("utf-8")
            except Exception:
                s = None
            if s:
                s_clean = s.strip()
                # hex string?
                if all(c in "0123456789abcdefABCDEF" for c in s_clean) and len(s_clean) in (64, 32, 48):
                    # support 32-byte (64 hex) or shorter keys (not recommended)
                    try:
                        k = binascii.unhexlify(s_clean)
                        if len(k) == _KEY_LEN:
                            return k
                    except Exception:
                        pass
            # else if file contains binary data of length 32 already, use it
            if len(raw) == _KEY_LEN:
                return raw
            # otherwise error
            raise ValueError("secret.hex exists but is not a valid 32-byte key or hex for 32 bytes")

    raise FileNotFoundError("No key source found: set AK_PASS, or create secret.pass or secret.hex")

def encrypt_bytes(plaintext: bytes) -> bytes:
    """
    Returns nonce (12 bytes) + ciphertext (ct includes tag)
    """
    key = load_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext, None)
    return nonce + ct

def decrypt_bytes(enc: bytes) -> bytes:
    key = load_key()
    aesgcm = AESGCM(key)
    if len(enc) < 12:
        raise ValueError("ciphertext too short")
    nonce = enc[:12]
    ct = enc[12:]
    return aesgcm.decrypt(nonce, ct, None)
