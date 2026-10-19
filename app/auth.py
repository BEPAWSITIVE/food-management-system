import hashlib
import secrets

def hash_password(password: str, salt: str = None) -> str:
    """Hash a password using SHA-256 and a random salt."""
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return f"{salt}${hashed}"

def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Verify password against stored salt$hash format."""
    try:
        salt, hashed = stored_hash.split('$')
        recomputed = hashlib.sha256((salt + plain_password).encode('utf-8')).hexdigest()
        return secrets.compare_digest(hashed, recomputed)
    except Exception:
        return False
