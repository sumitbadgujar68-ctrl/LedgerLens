import json
import os
import uuid
from decimal import Decimal
import pytest

from app.db.models import (
    Case,
    Entity,
    EntityAddress,
    Investigator,
    PatternRecord,
    RiskScoreRecord,
    TraceRun,
    VaspAttributionRecord,
)


def test_entity_and_address_instantiation():
    entity_id = uuid.uuid4()
    entity = Entity(
        entity_id=entity_id,
        name="Binance",
        entity_type="exchange",
        jurisdiction="International",
        website="https://binance.com",
        verification_level="verified",
    )
    assert entity.entity_id == entity_id
    assert entity.name == "Binance"
    assert entity.entity_type == "exchange"
    assert entity.verification_level == "verified"

    address_id = uuid.uuid4()
    address = EntityAddress(
        address_id=address_id,
        entity_id=entity_id,
        blockchain="ethereum",
        address="0x28c6c06298d514db089934071355e5743bf21d60",
        label="Binance 14 (Hot Wallet)",
        category="exchange_hot_wallet",
        source="etherscan_verified",
        confidence=Decimal("1.00"),
        metadata_={"verified_by": "sec_ops"},
    )
    assert address.address_id == address_id
    assert address.blockchain == "ethereum"
    assert address.confidence == Decimal("1.00")
    assert address.metadata_["verified_by"] == "sec_ops"


def test_pattern_record_instantiation():
    case_id = uuid.uuid4()
    trace_id = uuid.uuid4()
    pattern_id = uuid.uuid4()

    pattern = PatternRecord(
        pattern_id=pattern_id,
        case_id=case_id,
        trace_id=trace_id,
        wallet_address="0x1234567890123456789012345678901234567890",
        pattern_type="rapid_forwarding",
        confidence=Decimal("0.95"),
        description="Forwarded 95% of incoming volume within 4 minutes",
        evidence={
            "inbound_tx": "0xaaa",
            "outbound_tx": "0xbbb",
            "time_delta_seconds": 240,
        },
        metrics={"volume_eth": 10.5},
    )

    assert pattern.pattern_id == pattern_id
    assert pattern.pattern_type == "rapid_forwarding"
    assert pattern.confidence == Decimal("0.95")
    assert pattern.evidence["time_delta_seconds"] == 240


def test_vasp_attribution_record_instantiation():
    case_id = uuid.uuid4()
    trace_id = uuid.uuid4()
    entity_id = uuid.uuid4()
    attribution_id = uuid.uuid4()

    attribution = VaspAttributionRecord(
        attribution_id=attribution_id,
        case_id=case_id,
        trace_id=trace_id,
        wallet_address="0x28c6c06298d514db089934071355e5743bf21d60",
        candidate_entity_id=entity_id,
        provenance_level="DIRECT",
        confidence=Decimal("1.00"),
        attribution_method="registry_exact_match",
        evidence={"registry_entry": "Binance 14", "match_type": "exact"},
        source="etherscan_verified",
    )

    assert attribution.attribution_id == attribution_id
    assert attribution.provenance_level == "DIRECT"
    assert attribution.attribution_method == "registry_exact_match"
    assert attribution.confidence == Decimal("1.00")


def test_risk_score_record_instantiation():
    case_id = uuid.uuid4()
    trace_id = uuid.uuid4()
    risk_id = uuid.uuid4()

    risk = RiskScoreRecord(
        risk_score_id=risk_id,
        case_id=case_id,
        trace_id=trace_id,
        wallet_address="0x1234567890123456789012345678901234567890",
        score=78,
        risk_category="critical",
        scoring_version="v1.0.0",
        factors=[
            {"key": "PAT_RAPID_FWD", "delta": 20, "reason": "Rapid forwarding detected"},
            {"key": "PAT_FAN_OUT", "delta": 15, "reason": "High fan-out (8 recipients)"},
            {"key": "ENT_UNVERIFIED_HOP", "delta": 10, "reason": "Hop 3 unverified wallet"},
        ],
    )

    assert risk.risk_score_id == risk_id
    assert risk.score == 78
    assert risk.risk_category == "critical"
    assert risk.scoring_version == "v1.0.0"
    assert len(risk.factors) == 3


def test_seed_catalog_integrity():
    seed_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "database", "seeds", "entities_seed.json"
    )
    assert os.path.exists(seed_path), "Seed file must exist"

    with open(seed_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) >= 5, "Should have at least 5 curated seed entities"

    for entity in data:
        assert "name" in entity
        assert "entity_type" in entity
        assert entity["entity_type"] in [
            "exchange", "vasp", "mixer", "bridge", "defi_protocol", 
            "payment_processor", "scam_infrastructure", "known_contract", "unknown"
        ]
        assert "addresses" in entity
        assert isinstance(entity["addresses"], list)
        for addr in entity["addresses"]:
            assert "address" in addr
            assert addr["address"].startswith("0x")
            assert "confidence" in addr
            assert 0.0 <= addr["confidence"] <= 1.0
            assert "source" in addr
