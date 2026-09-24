from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from typing import Any, Dict, List, Optional


ENGINE_VERSION = "patterns-v1.0.0"


class PatternType(str, Enum):
    RAPID_FORWARDING = "rapid_forwarding"
    PEEL_CHAIN = "peel_chain"
    HIGH_FAN_OUT = "high_fan_out"
    HIGH_FAN_IN = "high_fan_in"
    CYCLIC_FLOW = "cyclic_flow"
    REPEATED_COUNTERPARTIES = "repeated_counterparties"
    VOLUME_CONCENTRATION = "volume_concentration"


@dataclass
class PatternFinding:
    pattern_type: PatternType
    wallet_address: str
    confidence: Decimal
    description: str
    evidence: Dict[str, Any]
    metrics: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.utcnow)
    engine_version: str = ENGINE_VERSION
