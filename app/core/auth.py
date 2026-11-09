import hashlib
import hmac
import secrets
import time
from typing import Any

from fastapi import Header, HTTPException, status

# In-memory admin user definition
ADMIN_USER = {
    "username": "admin",
    "email": "admin@email.com",
    # Pre-calculated salted SHA-256 for password '1234'
    "password_hash": hashlib.sha256(b"venticut_salt_1234").hexdigest(),
    "role": "superadmin",
}

# In-memory active session tokens store: {token: {"user": ..., "expires_at": ...}}
ACTIVE_SESSIONS: dict[str, dict[str, Any]] = {}
SESSION_EXPIRATION_SECONDS = 86400  # 24 hours


def verify_password(plain_password: str) -> bool:
    candidate_hash = hashlib.sha256(f"venticut_salt_{plain_password}".encode()).hexdigest()
    return hmac.compare_digest(candidate_hash, ADMIN_USER["password_hash"])


def create_admin_session() -> str:
    token = secrets.token_hex(32)
    ACTIVE_SESSIONS[token] = {
        "username": ADMIN_USER["username"],
        "email": ADMIN_USER["email"],
        "role": ADMIN_USER["role"],
        "expires_at": time.time() + SESSION_EXPIRATION_SECONDS,
    }
    return token


def invalidate_session(token: str) -> bool:
    if token in ACTIVE_SESSIONS:
        del ACTIVE_SESSIONS[token]
        return True
    return False


def get_current_admin(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in with admin credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'.",
        )

    session = ACTIVE_SESSIONS.get(token)
    if not session or time.time() > session["expires_at"]:
        if session:
            del ACTIVE_SESSIONS[token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please log in again.",
        )

    return session
