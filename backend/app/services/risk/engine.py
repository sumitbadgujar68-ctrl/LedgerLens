import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PatternRecord, RiskScoreRecord, VaspAttributionRecord
from app.services.entity.attribution_engine import AttributionEngine
from app.services.graph.model import CanonicalGraph
from app.services.patterns.engine import run_all_detectors
from app.services.risk.factors import RiskFactorCalculator
from app.services.risk.models import (
    SCORING_VERSION,
    RiskExplanation,
    RiskFactor,
    RiskFactorEvidence,
    RiskScore,
    categorize_score,
    validate_score,
)


class RiskEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.attribution_engine = AttributionEngine(db)

    async def calculate_risk(
        self,
        case_id: UUID,
        trace_id: UUID,
        graph: CanonicalGraph,
        wallet_address: str,
    ) -> RiskScore:
        patterns = run_all_detectors(graph)

        wallet_addresses = {n.id for n in graph.nodes}
        attributions = []
        for addr in wallet_addresses:
            for pattern in patterns:
                if pattern.wallet_address == addr:
                    attr = await self.attribution_engine.attribute_address(
                        addr, graph.blockchain, case_id, trace_id
                    )
                    if attr:
                        attributions.append(attr)

        existing_attributions = await self._get_existing_attributions(case_id, trace_id)
        attributions.extend(existing_attributions)

        calculator = RiskFactorCalculator(graph, patterns, attributions, self.db)
        factors = calculator.calculate_all(wallet_address)

        total_score = sum(f.weight for f in factors)
        total_score = validate_score(total_score)
        risk_category = categorize_score(total_score)

        risk_score = RiskScore(
            risk_score_id=str(uuid.uuid4()),
            case_id=str(case_id),
            trace_id=str(trace_id),
            wallet_address=wallet_address,
            score=total_score,
            risk_category=risk_category,
            scoring_version=SCORING_VERSION,
            factors=factors,
            calculated_at=datetime.utcnow(),
        )

        await self._persist_risk_score(risk_score)
        return risk_score

    async def calculate_all_wallets(
        self,
        case_id: UUID,
        trace_id: UUID,
        graph: CanonicalGraph,
    ) -> List[RiskScore]:
        results = []
        for node in graph.nodes:
            score = await self.calculate_risk(case_id, trace_id, graph, node.id)
            results.append(score)
        return results

    async def _get_existing_attributions(
        self, case_id: UUID, trace_id: UUID
    ) -> List[VaspAttributionRecord]:
        from sqlalchemy import select
        stmt = select(VaspAttributionRecord).where(
            VaspAttributionRecord.case_id == case_id,
            VaspAttributionRecord.trace_id == trace_id,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _persist_risk_score(self, risk_score: RiskScore) -> RiskScoreRecord:
        factors_json = []
        for f in risk_score.factors:
            factors_json.append({
                "factor_type": f.factor_type.value,
                "weight": f.weight,
                "evidence": {
                    "transaction_hashes": f.evidence.transaction_hashes,
                    "pattern_ids": f.evidence.pattern_ids,
                    "attribution_ids": f.evidence.attribution_ids,
                    "entity_ids": f.evidence.entity_ids,
                    "wallet_addresses": f.evidence.wallet_addresses,
                    "additional_data": f.evidence.additional_data,
                },
                "description": f.description,
                "confidence": str(f.confidence),
            })

        record = RiskScoreRecord(
            risk_score_id=UUID(risk_score.risk_score_id),
            case_id=UUID(risk_score.case_id),
            trace_id=UUID(risk_score.trace_id),
            wallet_address=risk_score.wallet_address,
            score=risk_score.score,
            risk_category=risk_score.risk_category.value,
            scoring_version=risk_score.scoring_version,
            factors=factors_json,
            calculated_at=risk_score.calculated_at,
        )

        self.db.add(record)
        await self.db.flush()
        return record

    async def get_risk_score(
        self, case_id: UUID, trace_id: UUID, wallet_address: str
    ) -> Optional[RiskScore]:
        from sqlalchemy import select
        stmt = select(RiskScoreRecord).where(
            RiskScoreRecord.case_id == case_id,
            RiskScoreRecord.trace_id == trace_id,
            RiskScoreRecord.wallet_address == wallet_address,
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            return None

        return self._record_to_risk_score(record)

    async def get_risk_explanation(
        self, case_id: UUID, trace_id: UUID, wallet_address: str
    ) -> Optional[RiskExplanation]:
        risk_score = await self.get_risk_score(case_id, trace_id, wallet_address)
        if not risk_score:
            return None

        factor_explanations = []
        for f in risk_score.factors:
            if f.weight > 0:
                evidence_parts = []
                if f.evidence.transaction_hashes:
                    evidence_parts.append(f"transactions: {', '.join(f.evidence.transaction_hashes[:3])}")
                if f.evidence.pattern_ids:
                    evidence_parts.append(f"patterns: {len(f.evidence.pattern_ids)}")
                if f.evidence.attribution_ids:
                    evidence_parts.append(f"attributions: {len(f.evidence.attribution_ids)}")
                if f.evidence.entity_ids:
                    evidence_parts.append(f"entities: {len(f.evidence.entity_ids)}")

                evidence_str = "; ".join(evidence_parts) if evidence_parts else "no specific evidence"
                factor_explanations.append(
                    f"{f.factor_type.value.replace('_', ' ').title()}: +{f.weight} ({evidence_str})"
                )

        summary = (
            f"Risk Score: {risk_score.score}/100 ({risk_score.risk_category.value.upper()})\n"
            f"Scoring Version: {risk_score.scoring_version}\n"
            f"Calculated: {risk_score.calculated_at.isoformat()}\n\n"
            f"Contributing Factors:\n" + "\n".join(factor_explanations)
        )

        return RiskExplanation(
            risk_score_id=risk_score.risk_score_id,
            wallet_address=risk_score.wallet_address,
            total_score=risk_score.score,
            risk_category=risk_score.risk_category,
            scoring_version=risk_score.scoring_version,
            factor_explanations=factor_explanations,
            summary=summary,
            calculated_at=risk_score.calculated_at,
        )

    def _record_to_risk_score(self, record: RiskScoreRecord) -> RiskScore:
        factors = []
        for f_data in record.factors:
            evidence = RiskFactorEvidence(
                transaction_hashes=f_data.get("evidence", {}).get("transaction_hashes", []),
                pattern_ids=f_data.get("evidence", {}).get("pattern_ids", []),
                attribution_ids=f_data.get("evidence", {}).get("attribution_ids", []),
                entity_ids=f_data.get("evidence", {}).get("entity_ids", []),
                wallet_addresses=f_data.get("evidence", {}).get("wallet_addresses", []),
                additional_data=f_data.get("evidence", {}).get("additional_data", {}),
            )
            factors.append(RiskFactor(
                factor_type=type('RiskFactorType', (), {'value': f_data["factor_type"]})(),
                weight=f_data["weight"],
                evidence=evidence,
                description=f_data["description"],
                confidence=Decimal(f_data["confidence"]),
            ))

        return RiskScore(
            risk_score_id=str(record.risk_score_id),
            case_id=str(record.case_id),
            trace_id=str(record.trace_id),
            wallet_address=record.wallet_address,
            score=record.score,
            risk_category=type('RiskCategory', (), {'value': record.risk_category})(),
            scoring_version=record.scoring_version,
            factors=factors,
            calculated_at=record.calculated_at,
        )


def get_risk_engine(db: AsyncSession) -> RiskEngine:
    return RiskEngine(db)