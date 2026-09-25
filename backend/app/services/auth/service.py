"""Credential verification against the investigators table (docs/API_CONTRACT.md 3.2)."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Investigator
from app.services.auth.security import create_access_token, verify_password


async def find_investigator(db: AsyncSession, username: str) -> Optional[Investigator]:
    result = await db.execute(
        select(Investigator).where(Investigator.username == username)
    )
    return result.scalar_one_or_none()


async def authenticate(
    db: AsyncSession, username: str, password: str
) -> Optional[Investigator]:
    investigator = await find_investigator(db, username)
    if investigator is None or not investigator.active:
        return None
    if not verify_password(password, investigator.password_hash):
        return None
    investigator.last_login = datetime.now(timezone.utc)
    await db.commit()
    return investigator


def issue_access_token(investigator: Investigator) -> str:
    return create_access_token(
        investigator_id=investigator.investigator_id,
        username=investigator.username,
        role=investigator.role,
    )


async def get_active_investigator(
    db: AsyncSession, investigator_id: UUID
) -> Optional[Investigator]:
    result = await db.execute(
        select(Investigator).where(Investigator.investigator_id == investigator_id)
    )
    investigator = result.scalar_one_or_none()
    if investigator is None or not investigator.active:
        return None
    return investigator
