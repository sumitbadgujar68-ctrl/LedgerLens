"""Request authentication and case ownership authorization (docs/SECURITY_MODEL.md 7.1, 7.2)."""

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.auth.security import (
    TokenExpired,
    TokenInvalid,
    decode_access_token,
)

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    investigator_id: UUID
    username: str
    full_name: str
    role: str


def unauthorized(code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": {"code": code, "message": message}},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> Principal:
    if credentials is None or not credentials.credentials:
        raise unauthorized(
            "AUTHENTICATION_REQUIRED",
            "Authentication required. Send 'Authorization: Bearer <token>'.",
        )
    try:
        claims = decode_access_token(credentials.credentials)
    except TokenExpired:
        raise unauthorized("TOKEN_EXPIRED", "Access token has expired.")
    except TokenInvalid:
        raise unauthorized("INVALID_TOKEN", "Access token is invalid.")

    subject = claims.get("sub")
    try:
        investigator_id = UUID(str(subject))
    except (ValueError, TypeError, AttributeError):
        raise unauthorized("INVALID_TOKEN", "Access token is invalid.")

    return Principal(
        investigator_id=investigator_id,
        username=str(claims.get("username", "")),
        full_name=str(claims.get("full_name", "")),
        role=str(claims.get("role", "")),
    )


async def require_auth(
    principal: Principal = Depends(get_current_principal),
) -> Principal:
    return principal


def case_access_denied(case_id: UUID) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "error": {
                "code": "CASE_ACCESS_DENIED",
                "message": f"Case {case_id} is not accessible for this investigator",
            }
        },
    )


def require_case_ownership(case, principal: Principal, case_id: UUID) -> None:
    if getattr(principal, "role", "") == "admin":
        return
    case_owner = getattr(case, "investigator_id", None)
    if case_owner and str(case_owner) != str(principal.investigator_id):
        raise case_access_denied(case_id)

