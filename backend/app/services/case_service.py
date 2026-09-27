from typing import Optional, Union
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.models import Case
from app.models.schemas import CaseCreate, CaseUpdate

class CaseService:
    
    @staticmethod
    async def create_case(db: AsyncSession, case_data: CaseCreate, investigator_id: UUID) -> Case:
        new_case = Case(
            title=case_data.title,
            reported_wallet_address=case_data.reported_wallet_address,
            reported_transaction_hash=case_data.reported_transaction_hash,
            blockchain=case_data.blockchain,
            fraud_type=case_data.fraud_type,
            reported_amount=case_data.reported_amount,
            reported_asset=case_data.reported_asset,
            reported_date=case_data.reported_date,
            investigator_notes=case_data.investigator_notes,
            investigator_id=investigator_id,
            case_number=""
        )
        db.add(new_case)
        await db.commit()
        await db.refresh(new_case)
        return new_case
    
    @staticmethod
    async def get_case(db: AsyncSession, case_id: Union[UUID, str]) -> Optional[Case]:
        if isinstance(case_id, UUID):
            result = await db.execute(select(Case).where(Case.case_id == case_id))
            return result.scalar_one_or_none()
        try:
            parsed_uuid = UUID(str(case_id))
            result = await db.execute(select(Case).where(Case.case_id == parsed_uuid))
            case = result.scalar_one_or_none()
            if case:
                return case
        except (ValueError, AttributeError):
            pass
        result = await db.execute(select(Case).where(Case.case_number == str(case_id)))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_case(db: AsyncSession, case_id: Union[UUID, str], case_update: CaseUpdate) -> Optional[Case]:
        case = await CaseService.get_case(db, case_id)
        if not case:
            return None
        actual_uuid = case.case_id
        update_data = case_update.model_dump(exclude_unset=True)
        if not update_data:
            return case
        
        await db.execute(
            update(Case)
            .where(Case.case_id == actual_uuid)
            .values(**update_data)
        )
        await db.commit()
        return await CaseService.get_case(db, actual_uuid)
    
    @staticmethod
    async def list_cases(db: AsyncSession, investigator_id: UUID, skip: int = 0, limit: int = 100):
        result = await db.execute(
            select(Case)
            .where(Case.investigator_id == investigator_id)
            .order_by(Case.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()