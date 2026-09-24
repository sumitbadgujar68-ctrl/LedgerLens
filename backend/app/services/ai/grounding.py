from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Case,
    Entity,
    EntityAddress,
    PatternRecord,
    RiskScoreRecord,
    TraceRun,
    TransactionRecord,
    VaspAttributionRecord,
)
from app.services.graph.model import CanonicalGraph
from app.services.risk.models import RiskFactor, RiskFactorEvidence, RiskScore


class GroundingLayer:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_case(self, case_id: UUID) -> Optional[Dict[str, Any]]:
        result = await self.db.execute(select(Case).where(Case.case_id == case_id))
        case = result.scalar_one_or_none()
        if not case:
            return None

        return {
            "case_id": str(case.case_id),
            "case_number": case.case_number,
            "title": case.title,
            "reported_wallet_address": case.reported_wallet_address,
            "reported_transaction_hash": case.reported_transaction_hash,
            "blockchain": case.blockchain,
            "fraud_type": case.fraud_type,
            "reported_amount": str(case.reported_amount) if case.reported_amount else None,
            "reported_asset": case.reported_asset,
            "reported_date": case.reported_date.isoformat() if case.reported_date else None,
            "status": case.status,
            "investigator_notes": case.investigator_notes,
            "created_at": case.created_at.isoformat(),
            "updated_at": case.updated_at.isoformat() if case.updated_at else None,
        }

    async def get_graph(self, case_id: UUID, trace_id: Optional[UUID] = None) -> Optional[CanonicalGraph]:
        from app.db.models import GraphRecord

        if trace_id:
            result = await self.db.execute(
                select(GraphRecord).where(GraphRecord.trace_id == trace_id)
            )
        else:
            result = await self.db.execute(
                select(GraphRecord)
                .where(GraphRecord.case_id == case_id)
                .order_by(GraphRecord.generated_at.desc())
                .limit(1)
            )
        graph_record = result.scalar_one_or_none()
        if not graph_record:
            return None

        return CanonicalGraph.model_validate(graph_record.graph_data)

    async def get_patterns(
        self, case_id: UUID, trace_id: Optional[UUID] = None, wallet_address: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = select(PatternRecord).where(PatternRecord.case_id == case_id)
        if trace_id:
            query = query.where(PatternRecord.trace_id == trace_id)
        if wallet_address:
            query = query.where(PatternRecord.wallet_address == wallet_address)
        query = query.order_by(PatternRecord.detected_at.desc())

        result = await self.db.execute(query)
        patterns = result.scalars().all()

        return [
            {
                "pattern_id": str(p.pattern_id),
                "pattern_type": p.pattern_type,
                "wallet_address": p.wallet_address,
                "confidence": str(p.confidence),
                "description": p.description,
                "evidence": p.evidence,
                "metrics": p.metrics,
                "detected_at": p.detected_at.isoformat(),
            }
            for p in patterns
        ]

    async def get_attributions(
        self, case_id: UUID, trace_id: Optional[UUID] = None, wallet_address: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = select(VaspAttributionRecord).where(VaspAttributionRecord.case_id == case_id)
        if trace_id:
            query = query.where(VaspAttributionRecord.trace_id == trace_id)
        if wallet_address:
            query = query.where(VaspAttributionRecord.wallet_address == wallet_address)
        query = query.order_by(VaspAttributionRecord.attributed_at.desc())

        result = await self.db.execute(query)
        attributions = result.scalars().all()

        enriched = []
        for a in attributions:
            entity_result = await self.db.execute(
                select(Entity).where(Entity.entity_id == a.candidate_entity_id)
            )
            entity = entity_result.scalar_one_or_none()
            enriched.append({
                "attribution_id": str(a.attribution_id),
                "wallet_address": a.wallet_address,
                "provenance_level": a.provenance_level,
                "confidence": str(a.confidence),
                "attribution_method": a.attribution_method,
                "evidence": a.evidence,
                "source": a.source,
                "attributed_at": a.attributed_at.isoformat(),
                "entity": {
                    "entity_id": str(entity.entity_id) if entity else None,
                    "name": entity.name if entity else None,
                    "entity_type": entity.entity_type if entity else None,
                    "verification_level": entity.verification_level if entity else None,
                } if entity else None,
            })
        return enriched

    async def get_risk_scores(
        self, case_id: UUID, trace_id: Optional[UUID] = None, wallet_address: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = select(RiskScoreRecord).where(RiskScoreRecord.case_id == case_id)
        if trace_id:
            query = query.where(RiskScoreRecord.trace_id == trace_id)
        if wallet_address:
            query = query.where(RiskScoreRecord.wallet_address == wallet_address)
        query = query.order_by(RiskScoreRecord.calculated_at.desc())

        result = await self.db.execute(query)
        risk_scores = result.scalars().all()

        return [
            {
                "risk_score_id": str(r.risk_score_id),
                "wallet_address": r.wallet_address,
                "score": r.score,
                "risk_category": r.risk_category,
                "scoring_version": r.scoring_version,
                "factors": r.factors,
                "calculated_at": r.calculated_at.isoformat(),
            }
            for r in risk_scores
        ]

    async def get_evidence(self, case_id: UUID) -> List[Dict[str, Any]]:
        from app.db.models import Evidence

        result = await self.db.execute(
            select(Evidence)
            .where(Evidence.case_id == case_id)
            .order_by(Evidence.pinned_at.desc())
        )
        evidence = result.scalars().all()

        return [
            {
                "evidence_id": str(e.evidence_id),
                "evidence_type": e.evidence_type,
                "reference_id": str(e.reference_id),
                "investigator_note": e.investigator_note,
                "investigator_id": str(e.investigator_id),
                "pinned_at": e.pinned_at.isoformat(),
            }
            for e in evidence
        ]

    async def get_transactions(
        self, case_id: UUID, trace_id: Optional[UUID] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        query = select(TransactionRecord).where(TransactionRecord.case_id == case_id)
        if trace_id:
            query = query.where(TransactionRecord.trace_id == trace_id)
        query = query.order_by(TransactionRecord.block_timestamp.desc()).limit(limit)

        result = await self.db.execute(query)
        transactions = result.scalars().all()

        return [
            {
                "transaction_id": str(t.transaction_id),
                "transaction_hash": t.transaction_hash,
                "block_number": t.block_number,
                "block_timestamp": t.block_timestamp.isoformat() if t.block_timestamp else None,
                "from_address": t.from_address,
                "to_address": t.to_address,
                "asset_symbol": t.asset_symbol,
                "amount": str(t.amount),
                "token_contract_address": t.token_contract_address,
                "transaction_type": t.transaction_type,
                "status": t.status,
                "discovered_at_hop": t.discovered_at_hop,
            }
            for t in transactions
        ]

    async def get_trace_runs(self, case_id: UUID) -> List[Dict[str, Any]]:
        result = await self.db.execute(
            select(TraceRun)
            .where(TraceRun.case_id == case_id)
            .order_by(TraceRun.created_at.desc())
        )
        traces = result.scalars().all()

        return [
            {
                "trace_id": str(t.trace_id),
                "start_wallet_address": t.start_wallet_address,
                "blockchain": t.blockchain,
                "direction": t.direction,
                "max_hops": t.max_hops,
                "max_branches": t.max_branches,
                "status": t.status,
                "result_status": t.result_status,
                "summary": t.summary,
                "created_at": t.created_at.isoformat(),
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            }
            for t in traces
        ]