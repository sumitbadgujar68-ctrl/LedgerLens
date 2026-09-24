import uuid
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PatternRecord
from app.services.graph.model import CanonicalGraph
from app.services.patterns.detectors import (
    detect_cyclic_flow,
    detect_high_fan_in,
    detect_high_fan_out,
    detect_peel_chain,
    detect_rapid_forwarding,
    detect_repeated_counterparties,
    detect_volume_concentration,
)
from app.services.patterns.models import PatternFinding, PatternType

_DETECTORS = [
    detect_rapid_forwarding,
    detect_peel_chain,
    detect_high_fan_out,
    detect_high_fan_in,
    detect_cyclic_flow,
    detect_repeated_counterparties,
    detect_volume_concentration,
]


def run_all_detectors(graph: CanonicalGraph) -> List[PatternFinding]:
    findings: List[PatternFinding] = []
    for detector in _DETECTORS:
        findings.extend(detector(graph))
    return findings


async def persist_findings(
    db: AsyncSession,
    findings: List[PatternFinding],
    case_id: UUID,
    trace_id: UUID,
) -> List[PatternRecord]:
    records: List[PatternRecord] = []
    for finding in findings:
        record = PatternRecord(
            pattern_id=uuid.uuid4(),
            case_id=case_id,
            trace_id=trace_id,
            wallet_address=finding.wallet_address,
            pattern_type=finding.pattern_type.value,
            confidence=finding.confidence,
            description=finding.description,
            evidence=finding.evidence,
            metrics=finding.metrics,
        )
        db.add(record)
        records.append(record)
    if records:
        await db.flush()
    return records
