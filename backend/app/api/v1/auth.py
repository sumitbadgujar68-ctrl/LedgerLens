"""Phase 7 — authentication endpoints (docs/API_CONTRACT.md section 3.2).

POST /api/v1/auth/login   — issue a JWT access token
POST /api/v1/auth/logout  — end the caller's session (authenticated)
GET  /api/v1/auth/me      — describe the authenticated investigator
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_db
from app.models.auth_schemas import (
    InvestigatorProfile,
    LoginRequest,
    LogoutResponse,
    SessionResponse,
    TokenResponse,
)
from app.models.schemas import ErrorResponse
from app.services.auth.deps import Principal, get_current_principal, unauthorized
from app.services.auth.service import (
    authenticate,
    get_active_investigator,
    issue_access_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        422: {"model": ErrorResponse, "description": "Invalid request body"},
    },
)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Exchange username/password credentials for a JWT access token."""
    investigator = await authenticate(db, request.username, request.password)
    if investigator is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid username or password",
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    profile = InvestigatorProfile(
        investigator_id=investigator.investigator_id,
        username=investigator.username,
        full_name=investigator.full_name,
        role=investigator.role,
    )
    return TokenResponse(
        access_token=issue_access_token(investigator),
        expires_in=settings.access_token_expire_minutes * 60,
        investigator=profile,
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    responses={401: {"model": ErrorResponse, "description": "Authentication required"}},
)
async def logout(principal: Principal = Depends(get_current_principal)):
    """End the caller's session (stateless JWT bearer tokens are not replayed)."""
    return LogoutResponse(message="Successfully logged out")


@router.get(
    "/me",
    response_model=SessionResponse,
    responses={401: {"model": ErrorResponse, "description": "Authentication required"}},
)
async def me(
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
):
    """Return the authenticated investigator's profile."""
    investigator = await get_active_investigator(db, principal.investigator_id)
    if investigator is None:
        raise unauthorized("INVALID_TOKEN", "Access token is invalid.")

    return SessionResponse(
        investigator_id=investigator.investigator_id,
        username=investigator.username,
        full_name=investigator.full_name,
        role=investigator.role,
        created_at=investigator.created_at,
        last_login=investigator.last_login,
    )
