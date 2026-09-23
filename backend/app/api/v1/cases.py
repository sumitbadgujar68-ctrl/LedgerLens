from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.schemas import CaseCreate, CaseResponse, CaseUpdate
from app.services.case_service import CaseService
from typing import List
from uuid import UUID

router = APIRouter(prefix="/cases", tags=["cases"])

MOCK_INVESTIGATOR_ID = UUID("00000000-0000-0000-0000-000000000001")

@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_data: CaseCreate,
    db: AsyncSession = Depends(get_db)
):
    case = await CaseService.create_case(db, case_data, MOCK_INVESTIGATOR_ID)
    return case

@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    case = await CaseService.get_case(db, case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CASE_NOT_FOUND",
                    "message": f"Case {case_id} not found"
                }
            }
        )
    return case

@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: UUID,
    case_update: CaseUpdate,
    db: AsyncSession = Depends(get_db)
):
    case = await CaseService.update_case(db, case_id, case_update)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CASE_NOT_FOUND",
                    "message": f"Case {case_id} not found"
                }
            }
        )
    return case

@router.get("", response_model=List[CaseResponse])
async def list_cases(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    cases = await CaseService.list_cases(db, MOCK_INVESTIGATOR_ID, skip, limit)
    return cases
