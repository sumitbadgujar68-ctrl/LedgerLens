"""MVP findings API — read endpoints for case patterns, evidence and attributions.

Implements the documented read contracts (docs/API_CONTRACT.md 4.5 and 4.7)
plus an attribution listing over the existing vasp_attributions schema:

    GET /api/v1/cases/{case_id}/patterns
    GET /api/v1/cases/{case_id}/evidence
    GET /api/v1/cases/{case_id}/attributions

Every serialized row carries ``demo_data`` and ``finding_source`` so the UI can
badge synthetic demonstration findings separately from findings derived from a
live provider trace. These endpoints never fabricate on-chain data — they only
read rows that already exist.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.db.models import Case, Evidence, PatternRecord, VaspAttributionRecord
from app.models.findings_schemas import (
    AttributionItem,
    AttributionListResponse,
    EvidenceItem,
    EvidenceListResponse,
    PatternItem,
    PatternListResponse,
)
from app.services.auth.deps import (
    Principal,
    get_current_principal,
    require_case_ownership,
)
from app.services.case_service import CaseService

logger = logging.getLogger("ledgerlens.api.findings")

router = APIRouter(prefix="/cases", tags=["findings"])

DEMO_MARKER = "DEMO DATA |"
DEMO_EVIDENCE_TRUE = "demo_data=true"
DEMO_EVIDENCE_FALSE = "demo_data=false"


def _case_not_found(case_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": {"code": "CASE_NOT_FOUND", "message": f"Case {case_id} not found"}},
    )


async def _require_access(
    db: AsyncSession, case_id: str, principal: Principal
) -> Case:
    case = await CaseService.get_case(db, case_id)
    if not case:
        raise _case_not_found(case_id)
    require_case_ownership(case, principal, case.case_id)
    return case


def _pattern_is_demo(record: PatternRecord) -> bool:
    metrics = record.metrics or {}
    evidence = record.evidence or {}
    return bool(
        metrics.get("demo_data")
        or evidence.get("demo_data")
        or (record.description or "").lstrip().startswith(DEMO_MARKER)
    )


def _evidence_is_demo(record: Evidence) -> bool:
    note = (record.investigator_note or "").lower()
    return DEMO_EVIDENCE_TRUE in note and DEMO_EVIDENCE_FALSE not in note


@router.get(
    "/{case_id}/patterns",
    response_model=PatternListResponse,
    responses={404: {"description": "Case not found"}},
)
async def list_patterns(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    """List detected patterns (live-trace-derived and labelled demo rows)."""
    case = await _require_access(db, case_id, principal)
    result = await db.execute(
        select(PatternRecord)
        .where(PatternRecord.case_id == case.case_id)
        .order_by(PatternRecord.detected_at.desc())
    )
    rows = result.scalars().all()
    items = []
    for row in rows:
        demo = _pattern_is_demo(row)
        metrics = row.metrics or {}
        items.append(
            PatternItem(
                pattern_id=row.pattern_id,
                trace_id=row.trace_id,
                wallet_address=row.wallet_address,
                pattern_type=row.pattern_type,
                demo_label=metrics.get("demo_label"),
                confidence=float(row.confidence),
                description=row.description,
                metrics=metrics,
                detected_at=row.detected_at,
                demo_data=demo,
                finding_source="demo" if demo else "live_trace_derived",
            )
        )
    return PatternListResponse(patterns=items)


@router.get(
    "/{case_id}/evidence",
    response_model=EvidenceListResponse,
    responses={404: {"description": "Case not found"}},
)
async def list_evidence(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    """List pinned evidence rows for the case with demo/live provenance."""
    case = await _require_access(db, case_id, principal)
    result = await db.execute(
        select(Evidence)
        .where(Evidence.case_id == case.case_id)
        .order_by(Evidence.pinned_at.desc())
    )
    rows = result.scalars().all()
    items = []
    for row in rows:
        demo = _evidence_is_demo(row)
        items.append(
            EvidenceItem(
                evidence_id=row.evidence_id,
                evidence_type=row.evidence_type,
                reference_id=row.reference_id,
                investigator_note=row.investigator_note,
                pinned_at=row.pinned_at,
                demo_data=demo,
                finding_source="demo" if demo else "live_on_chain",
            )
        )
    return EvidenceListResponse(evidence=items)


@router.get(
    "/{case_id}/attributions",
    response_model=AttributionListResponse,
    responses={404: {"description": "Case not found"}},
)
async def list_attributions(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    """List VASP/entity attributions recorded for the case's traces."""
    case = await _require_access(db, case_id, principal)
    result = await db.execute(
        select(VaspAttributionRecord)
        .options(selectinload(VaspAttributionRecord.candidate_entity))
        .where(VaspAttributionRecord.case_id == case.case_id)
        .order_by(VaspAttributionRecord.attributed_at.desc())
    )
    rows = result.scalars().all()
    items = []
    for row in rows:
        evidence = row.evidence or {}
        demo = bool(evidence.get("demo_data")) or row.source == "demo_seed"
        entity = row.candidate_entity
        items.append(
            AttributionItem(
                attribution_id=row.attribution_id,
                trace_id=row.trace_id,
                wallet_address=row.wallet_address,
                entity_id=row.candidate_entity_id,
                entity_name=entity.name if entity else "UNKNOWN",
                entity_type=entity.entity_type if entity else None,
                provenance_level=row.provenance_level,
                confidence=float(row.confidence),
                attribution_method=row.attribution_method,
                source=row.source,
                attributed_at=row.attributed_at,
                demo_data=demo,
                finding_source="demo" if demo else "registry_label",
                disclaimer=evidence.get("disclaimer"),
            )
        )
    return AttributionListResponse(attributions=items)
