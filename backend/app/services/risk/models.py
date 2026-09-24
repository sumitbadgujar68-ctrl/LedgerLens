from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


SCORING_VERSION = "v1.0.0"


class RiskCategory(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskFactorType(str, Enum):
    KNOWN_MALICIOUS_ASSOCIATION = "known_malicious_association"
    RAPID_ONWARD_TRANSFER = "rapid_onward_transfer"
    HIGH_FAN_IN = "high_fan_in"
    LAYERING_PEEL_CHAIN = "layering_peel_chain"
    MIXER_INTERACTION = "mixer_interaction"
    REPEATED_CASE_LINKAGE = "repeated_case_linkage"


DEFAULT_WEIGHTS: Dict[RiskFactorType, int] = {
    RiskFactorType.KNOWN_MALICIOUS_ASSOCIATION: 25,
    RiskFactorType.RAPID_ONWARD_TRANSFER: 20,
    RiskFactorType.HIGH_FAN_IN: 15,
    RiskFactorType.LAYERING_PEEL_CHAIN: 12,
    RiskFactorType.MIXER_INTERACTION: 10,
    RiskFactorType.REPEATED_CASE_LINKAGE: 5,
}


RISK_CATEGORY_THRESHOLDS = {
    RiskCategory.LOW: (0, 39),
    RiskCategory.MEDIUM: (40, 69),
    RiskCategory.HIGH: (70, 89),
    RiskCategory.CRITICAL: (90, 100),
}


@dataclass
class RiskFactorEvidence:
    transaction_hashes: List[str] = field(default_factory=list)
    pattern_ids: List[str] = field(default_factory=list)
    attribution_ids: List[str] = field(default_factory=list)
    entity_ids: List[str] = field(default_factory=list)
    wallet_addresses: List[str] = field(default_factory=list)
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskFactor:
    factor_type: RiskFactorType
    weight: int
    evidence: RiskFactorEvidence
    description: str
    confidence: Decimal = Decimal("1.00")


@dataclass
class RiskScore:
    risk_score_id: str
    case_id: str
    trace_id: str
    wallet_address: str
    score: int
    risk_category: RiskCategory
    scoring_version: str
    factors: List[RiskFactor]
    calculated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RiskExplanation:
    risk_score_id: str
    wallet_address: str
    total_score: int
    risk_category: RiskCategory
    scoring_version: str
    factor_explanations: List[str]
    summary: str
    calculated_at: datetime


def categorize_score(score: int) -> RiskCategory:
    score = validate_score(score)
    for category, (min_val, max_val) in RISK_CATEGORY_THRESHOLDS.items():
        if min_val <= score <= max_val:
            return category
    return RiskCategory.LOW


def validate_score(score: int) -> int:
    return max(0, min(100, score))