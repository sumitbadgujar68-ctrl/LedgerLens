from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RiskFactorEvidenceResponse(BaseModel):
    transaction_hashes: List[str] = Field(default_factory=list)
    pattern_ids: List[str] = Field(default_factory=list)
    attribution_ids: List[str] = Field(default_factory=list)
    entity_ids: List[str] = Field(default_factory=list)
    wallet_addresses: List[str] = Field(default_factory=list)
    additional_data: Dict[str, Any] = Field(default_factory=dict)


class RiskFactorResponse(BaseModel):
    factor_type: str
    weight: int
    evidence: RiskFactorEvidenceResponse
    description: str
    confidence: Decimal


class RiskScoreResponse(BaseModel):
    risk_score_id: UUID
    case_id: UUID
    trace_id: UUID
    wallet_address: str
    score: int
    risk_category: str
    scoring_version: str
    factors: List[RiskFactorResponse]
    calculated_at: datetime


class RiskExplanationResponse(BaseModel):
    risk_score_id: UUID
    wallet_address: str
    total_score: int
    risk_category: str
    scoring_version: str
    factor_explanations: List[str]
    summary: str
    calculated_at: datetime


class RiskSummaryResponse(BaseModel):
    case_id: UUID
    trace_id: UUID
    wallet_count: int
    risk_distribution: Dict[str, int]
    highest_risk_wallet: Optional[str] = None
    highest_risk_score: Optional[int] = None
    average_score: Optional[float] = None