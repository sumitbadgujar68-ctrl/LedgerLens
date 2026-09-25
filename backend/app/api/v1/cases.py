from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.schemas import CaseCreate, CaseResponse, CaseUpdate
from app.services.auth.deps import (
    Principal,
    get_current_principal,
    require_case_ownership,
)
from app.services.case_service import CaseService
from typing import List
from uuid import UUID

router = APIRouter(prefix="/cases", tags=["cases"])

MOCK_INVESTIGATOR_ID = UUID("00000000-0000-0000-0000-000000000001")

def _case_not_found(case_id: UUID) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "error": {
                "code": "CASE_NOT_FOUND",
                "message": f"Case {case_id} not found"
            }
        }
    )

@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_data: CaseCreate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    case = await CaseService.create_case(db, case_data, principal.investigator_id)
    return case

@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    case = await CaseService.get_case(db, case_id)
    if not case:
        raise _case_not_found(case_id)
    require_case_ownership(case, principal, case_id)
    return case

@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: UUID,
    case_update: CaseUpdate,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    case = await CaseService.get_case(db, case_id)
    if not case:
        raise _case_not_found(case_id)
    require_case_ownership(case, principal, case_id)
    return await CaseService.update_case(db, case_id, case_update)

@router.get("", response_model=List[CaseResponse])
async def list_cases(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    cases = await CaseService.list_cases(db, principal.investigator_id, skip, limit)
    return cases
