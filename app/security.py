"""Password hashing and signed session tokens.

Passwords: argon2 (D1). Never store or log a plain password.
Sessions: a signed (not encrypted) cookie via itsdangerous, carrying user id and
role. Signed cookies can be read by the client but not forged without SECRET_KEY.
"""
from __future__ import annotations

import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app import settings

SESSION_COOKIE = "cms_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

_hasher = PasswordHasher()
_serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="cms-session")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def create_session_token(user_id: int, role: str) -> str:
    """The csrf field is a random token minted once at login and carried in the
    signed cookie — every state-changing form (T03 onward) echoes it back."""
    return _serializer.dumps(
        {"user_id": user_id, "role": role, "csrf": secrets.token_urlsafe(24)}
    )


def read_session_token(token: str) -> dict | None:
    try:
        return _serializer.loads(token, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
