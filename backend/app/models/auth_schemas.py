from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


class InvestigatorProfile(BaseModel):
    investigator_id: UUID
    username: str
    full_name: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    investigator: InvestigatorProfile


class SessionResponse(InvestigatorProfile):
    created_at: datetime
    last_login: Optional[datetime] = None


class LogoutResponse(BaseModel):
    message: str
