"""Read models for case findings: patterns, evidence and attributions.

Each item carries an explicit ``demo_data`` flag and a ``finding_source`` so the
UI can badge synthetic demonstration rows (DEMO DATA) separately from rows
derived from live chain traces (LIVE ON-CHAIN). No on-chain fact is synthesized
here; these endpoints only serialize rows that already exist in the schema.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class PatternItem(BaseModel):
    pattern_id: UUID
    trace_id: UUID
    wallet_address: str
    pattern_type: str
    demo_label: Optional[str] = None
    confidence: float
    description: str
    metrics: dict = {}
    detected_at: datetime
    demo_data: bool
    finding_source: str


class PatternListResponse(BaseModel):
    patterns: List[PatternItem]


class EvidenceItem(BaseModel):
    evidence_id: UUID
    evidence_type: str
    reference_id: Optional[UUID]
    investigator_note: Optional[str]
    pinned_at: datetime
    demo_data: bool
    finding_source: str


class EvidenceListResponse(BaseModel):
    evidence: List[EvidenceItem]


class AttributionItem(BaseModel):
    attribution_id: UUID
    trace_id: UUID
    wallet_address: str
    entity_id: UUID
    entity_name: str
    entity_type: Optional[str] = None
    provenance_level: str
    confidence: float
    attribution_method: str
    source: str
    attributed_at: datetime
    demo_data: bool
    finding_source: str
    disclaimer: Optional[str] = None


class AttributionListResponse(BaseModel):
    attributions: List[AttributionItem]
