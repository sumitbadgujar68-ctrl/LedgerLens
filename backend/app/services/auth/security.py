"""Password hashing and JWT access tokens (docs/SECURITY_MODEL.md 5.1, docs/API_CONTRACT.md 3.1)."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
from jose import ExpiredSignatureError, JWTError, jwt

from app.config import settings


class TokenExpired(Exception):
    """Access token is past its expiry."""


class TokenInvalid(Exception):
    """Access token is malformed, unsigned with the wrong key, or otherwise unusable."""


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def create_access_token(
    investigator_id: UUID,
    username: str,
    role: str,
    expires_minutes: int | None = None,
) -> str:
    minutes = (
        expires_minutes
        if expires_minutes is not None
        else settings.access_token_expire_minutes
    )
    issued_at = datetime.now(timezone.utc)
    payload = {
        "sub": str(investigator_id),
        "username": username,
        "role": role,
        "typ": "access",
        "iat": issued_at,
        "exp": issued_at + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except ExpiredSignatureError as exc:
        raise TokenExpired() from exc
    except JWTError as exc:
        raise TokenInvalid() from exc
