from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.models import Case
from app.models.schemas import CaseCreate, CaseUpdate
from typing import Optional
from uuid import UUID

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
    async def get_case(db: AsyncSession, case_id: UUID) -> Optional[Case]:
        result = await db.execute(
            select(Case).where(Case.case_id == case_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_case(db: AsyncSession, case_id: UUID, case_update: CaseUpdate) -> Optional[Case]:
        update_data = case_update.model_dump(exclude_unset=True)
        if not update_data:
            return await CaseService.get_case(db, case_id)
        
        await db.execute(
            update(Case)
            .where(Case.case_id == case_id)
            .values(**update_data)
        )
        await db.commit()
        return await CaseService.get_case(db, case_id)
    
    @staticmethod
    async def list_cases(db: AsyncSession, investigator_id: UUID, skip: int = 0, limit: int = 20):
        result = await db.execute(
            select(Case)
            .where(Case.investigator_id == investigator_id)
            .order_by(Case.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
