import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Case, GraphRecord, RiskScoreRecord, TraceRun
from app.models.risk_schemas import (
    RiskExplanationResponse,
    RiskScoreResponse,
    RiskSummaryResponse,
)
from app.services.auth.deps import (
    Principal,
    get_current_principal,
    require_case_ownership,
)
from app.services.graph.model import CanonicalGraph
from app.services.risk.engine import RiskEngine
from app.services.tracing.service import TraceService

logger = logging.getLogger("ledgerlens.api.risk")

router = APIRouter(prefix="/cases", tags=["risk"])


def _build_risk_response(record: RiskScoreRecord) -> RiskScoreResponse:
    factors = []
    for f_data in record.factors:
        evidence = f_data.get("evidence", {})
        factors.append({
            "factor_type": f_data["factor_type"],
            "weight": f_data["weight"],
            "evidence": {
                "transaction_hashes": evidence.get("transaction_hashes", []),
                "pattern_ids": evidence.get("pattern_ids", []),
                "attribution_ids": evidence.get("attribution_ids", []),
                "entity_ids": evidence.get("entity_ids", []),
                "wallet_addresses": evidence.get("wallet_addresses", []),
                "additional_data": evidence.get("additional_data", {}),
            },
            "description": f_data["description"],
            "confidence": f_data["confidence"],
        })

    return RiskScoreResponse(
        risk_score_id=record.risk_score_id,
        case_id=record.case_id,
        trace_id=record.trace_id,
        wallet_address=record.wallet_address,
        score=record.score,
        risk_category=record.risk_category,
        scoring_version=record.scoring_version,
        factors=factors,
        calculated_at=record.calculated_at,
    )


def _build_explanation_response(record: RiskScoreRecord) -> RiskExplanationResponse:
    factor_explanations = []
    for f_data in record.factors:
        if f_data["weight"] > 0:
            evidence = f_data.get("evidence", {})
            evidence_parts = []
            if evidence.get("transaction_hashes"):
                evidence_parts.append(f"transactions: {', '.join(evidence['transaction_hashes'][:3])}")
            if evidence.get("pattern_ids"):
                evidence_parts.append(f"patterns: {len(evidence['pattern_ids'])}")
            if evidence.get("attribution_ids"):
                evidence_parts.append(f"attributions: {len(evidence['attribution_ids'])}")
            if evidence.get("entity_ids"):
                evidence_parts.append(f"entities: {len(evidence['entity_ids'])}")

            evidence_str = "; ".join(evidence_parts) if evidence_parts else "no specific evidence"
            factor_explanations.append(
                f"{f_data['factor_type'].replace('_', ' ').title()}: +{f_data['weight']} ({evidence_str})"
            )

    summary = (
        f"Risk Score: {record.score}/100 ({record.risk_category.upper()})\n"
        f"Scoring Version: {record.scoring_version}\n"
        f"Calculated: {record.calculated_at.isoformat()}\n\n"
        f"Contributing Factors:\n" + "\n".join(factor_explanations)
    )

    return RiskExplanationResponse(
        risk_score_id=record.risk_score_id,
        wallet_address=record.wallet_address,
        total_score=record.score,
        risk_category=record.risk_category,
        scoring_version=record.scoring_version,
        factor_explanations=factor_explanations,
        summary=summary,
        calculated_at=record.calculated_at,
    )


@router.get("/{case_id}/wallets/{wallet_address}/risk", response_model=RiskScoreResponse)
async def get_wallet_risk(
    case_id: UUID,
    wallet_address: str,
    trace_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    case = await db.execute(select(Case).where(Case.case_id == case_id))
    case_obj = case.scalar_one_or_none()
    if not case_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": f"Case {case_id} not found"}},
        )
    require_case_ownership(case_obj, principal, case_id)

    trace: Optional[TraceRun] = None
    if trace_id:
        trace_result = await db.execute(
            select(TraceRun).where(TraceRun.case_id == case_id, TraceRun.trace_id == trace_id)
        )
        trace = trace_result.scalar_one_or_none()
        if not trace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "TRACE_NOT_FOUND", "message": f"Trace {trace_id} not found"}},
            )
    else:
        traces_result = await db.execute(
            select(TraceRun)
            .where(TraceRun.case_id == case_id)
            .order_by(TraceRun.created_at.desc())
            .limit(1)
        )
        trace = traces_result.scalar_one_or_none()
        if not trace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "NO_TRACE", "message": f"No trace found for case {case_id}"}},
            )

    risk_result = await db.execute(
        select(RiskScoreRecord).where(
            RiskScoreRecord.case_id == case_id,
            RiskScoreRecord.trace_id == trace.trace_id,
            RiskScoreRecord.wallet_address == wallet_address.lower(),
        )
    )
    risk_record = risk_result.scalar_one_or_none()

    if not risk_record:
        risk_engine = RiskEngine(db)
        graph_row = await db.execute(select(GraphRecord).where(GraphRecord.trace_id == trace.trace_id))
        graph_record = graph_row.scalar_one_or_none()

        if not graph_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "GRAPH_NOT_FOUND", "message": f"Graph not found for trace {trace.trace_id}"}},
            )

        graph = CanonicalGraph.model_validate(graph_record.graph_data)
        risk_score = await risk_engine.calculate_risk(case_id, trace.trace_id, graph, wallet_address)
        return _build_risk_response(
            await db.execute(
                select(RiskScoreRecord).where(RiskScoreRecord.risk_score_id == risk_score.risk_score_id)
            )
        ).scalar_one()

    return _build_risk_response(risk_record)


@router.get("/risk/{risk_id}/explanation", response_model=RiskExplanationResponse)
async def get_risk_explanation(
    risk_id: UUID,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    risk_result = await db.execute(
        select(RiskScoreRecord).where(RiskScoreRecord.risk_score_id == risk_id)
    )
    risk_record = risk_result.scalar_one_or_none()

    if not risk_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "RISK_NOT_FOUND", "message": f"Risk score {risk_id} not found"}},
        )

    case_result = await db.execute(
        select(Case).where(Case.case_id == risk_record.case_id)
    )
    require_case_ownership(
        case_result.scalar_one_or_none(), principal, risk_record.case_id
    )

    return _build_explanation_response(risk_record)


@router.get("/{case_id}/risk-summary", response_model=RiskSummaryResponse)
async def get_case_risk_summary(
    case_id: UUID,
    trace_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    case = await db.execute(select(Case).where(Case.case_id == case_id))
    case_obj = case.scalar_one_or_none()
    if not case_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": f"Case {case_id} not found"}},
        )
    require_case_ownership(case_obj, principal, case_id)

    trace: Optional[TraceRun] = None
    if trace_id:
        trace_result = await db.execute(
            select(TraceRun).where(TraceRun.case_id == case_id, TraceRun.trace_id == trace_id)
        )
        trace = trace_result.scalar_one_or_none()
        if not trace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "TRACE_NOT_FOUND", "message": f"Trace {trace_id} not found"}},
            )
    else:
        traces_result = await db.execute(
            select(TraceRun)
            .where(TraceRun.case_id == case_id)
            .order_by(TraceRun.created_at.desc())
            .limit(1)
        )
        trace = traces_result.scalar_one_or_none()
        if not trace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "NO_TRACE", "message": f"No trace found for case {case_id}"}},
            )

    risk_result = await db.execute(
        select(RiskScoreRecord).where(
            RiskScoreRecord.case_id == case_id,
            RiskScoreRecord.trace_id == trace.trace_id,
        )
    )
    risk_records = risk_result.scalars().all()

    if not risk_records:
        risk_engine = RiskEngine(db)
        graph_row = await db.execute(select(GraphRecord).where(GraphRecord.trace_id == trace.trace_id))
        graph_record = graph_row.scalar_one_or_none()

        if not graph_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "GRAPH_NOT_FOUND", "message": f"Graph not found for trace {trace.trace_id}"}},
            )

        graph = CanonicalGraph.model_validate(graph_record.graph_data)
        await risk_engine.calculate_all_wallets(case_id, trace.trace_id, graph)

        risk_result = await db.execute(
            select(RiskScoreRecord).where(
                RiskScoreRecord.case_id == case_id,
                RiskScoreRecord.trace_id == trace.trace_id,
            )
        )
        risk_records = risk_result.scalars().all()

    risk_distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    highest_risk_score = 0
    highest_risk_wallet = None
    total_score = 0

    for r in risk_records:
        risk_distribution[r.risk_category] += 1
        total_score += r.score
        if r.score > highest_risk_score:
            highest_risk_score = r.score
            highest_risk_wallet = r.wallet_address

    return RiskSummaryResponse(
        case_id=case_id,
        trace_id=trace.trace_id,
        wallet_count=len(risk_records),
        risk_distribution=risk_distribution,
        highest_risk_wallet=highest_risk_wallet,
        highest_risk_score=highest_risk_score if risk_records else None,
        average_score=round(total_score / len(risk_records), 2) if risk_records else None,
    )