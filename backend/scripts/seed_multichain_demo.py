"""Seed LedgerLens with clearly-labelled MVP demo data (Phases 5-10).

Everything this script writes is either

* real Ethereum Mainnet data pulled through the live Alchemy provider
  (labelled ``LIVE ON-CHAIN``), or
* synthetic demonstration metadata (labelled ``DEMO DATA``).

The two are never mixed silently: every synthetic row carries an explicit
``demo_data`` marker so the UI can badge it. No on-chain fact (transaction hash,
block number, amount, balance) is ever invented here.

Usage (from the backend directory):

    python scripts/seed_demo_data.py                 # seed / refresh
    python scripts/seed_demo_data.py --reset         # remove seeded rows first
    python scripts/seed_demo_data.py --skip-live     # no provider calls
"""

import argparse
import asyncio
import json
import sys
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy import delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session_maker
from app.db.models import (
    Case,
    Entity,
    EntityAddress,
    Evidence,
    GraphRecord,
    Investigator,
    JobRecord,
    PatternRecord,
    ReportRecord,
    RiskScoreRecord,
    TraceRun,
    VaspAttributionRecord,
)
from app.models.schemas import CaseCreate
from app.services.blockchain import AlchemyProvider, EthereumAdapter, TransferDirection
from app.services.case_service import CaseService
from app.services.entity.attribution_engine import AttributionEngine
from app.services.graph.model import CanonicalGraph, TraceConfig
from app.services.patterns.engine import persist_findings, run_all_detectors
from app.services.reporting.generator import ReportGenerator
from app.services.reporting.store import ReportStore
from app.services.risk.engine import RiskEngine
from app.services.tracing.service import TraceService

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_INVESTIGATOR_USERNAME = "demo@ledgerlens.local"

REAL_ENTITY_SEED = Path(__file__).resolve().parents[2] / "database" / "seeds" / "entities_seed.json"

DEMO_SOURCE = "demo_seed"
DEMO_FINDING_SOURCE = "synthetic_demo"

def _demo_address(suffix: str) -> str:
    """A clearly non-real, reserved-range demo address (not a live account)."""
    return "0x" + ("0" * (40 - len(suffix))) + suffix


DEMO_ENTITIES: List[Dict[str, Any]] = [
    {
        "name": "DEMO_EXCHANGE_A",
        "entity_type": "exchange",
        "jurisdiction": "Demo jurisdiction (synthetic)",
        "website": None,
        "verification_level": "unverified",
        "addresses": [
            {
                "blockchain": "ethereum",
                "address": _demo_address("de01"),
                "label": "DEMO_EXCHANGE_A demo hot wallet (synthetic)",
                "category": "exchange_hot_wallet",
                "confidence": 0.50,
            }
        ],
    },
    {
        "name": "DEMO_EXCHANGE_B",
        "entity_type": "exchange",
        "jurisdiction": "Demo jurisdiction (synthetic)",
        "website": None,
        "verification_level": "unverified",
        "addresses": [
            {
                "blockchain": "ethereum",
                "address": _demo_address("de02"),
                "label": "DEMO_EXCHANGE_B demo deposit address (synthetic)",
                "category": "exchange_deposit",
                "confidence": 0.50,
            }
        ],
    },
    {
        "name": "DEMO_CUSTODIAL_SERVICE",
        "entity_type": "vasp",
        "jurisdiction": "Demo jurisdiction (synthetic)",
        "website": None,
        "verification_level": "unverified",
        "addresses": [
            {
                "blockchain": "ethereum",
                "address": _demo_address("de03"),
                "label": "DEMO_CUSTODIAL_SERVICE demo vault (synthetic)",
                "category": "custodial_vault",
                "confidence": 0.50,
            }
        ],
    },
]

# Requested demo pattern labels mapped onto the schema's allowed pattern_type
# CHECK values. The requested label is preserved in metrics.demo_label.
DEMO_PATTERNS = [
    {
        "demo_label": "HIGH_TRANSACTION_VELOCITY",
        "pattern_type": "rapid_forwarding",
        "description": (
            "DEMO DATA | synthetic_demo | demo_label=HIGH_TRANSACTION_VELOCITY. "
            "Demonstration pattern row seeded for MVP UI verification; the underlying "
            "transaction counts shown in metrics are read from the real trace graph."
        ),
    },
    {
        "demo_label": "REPEATED_COUNTERPARTY",
        "pattern_type": "repeated_counterparties",
        "description": (
            "DEMO DATA | synthetic_demo | demo_label=REPEATED_COUNTERPARTY. "
            "Demonstration pattern row seeded for MVP UI verification; the counterparty "
            "counts shown in metrics are read from the real trace graph."
        ),
    },
    {
        "demo_label": "RAPID_FUND_MOVEMENT",
        "pattern_type": "peel_chain",
        "description": (
            "DEMO DATA | synthetic_demo | demo_label=RAPID_FUND_MOVEMENT. "
            "Demonstration pattern row seeded for MVP UI verification."
        ),
    },
    {
        "demo_label": "UNUSUAL_TRANSACTION_CLUSTER",
        "pattern_type": "volume_concentration",
        "description": (
            "DEMO DATA | synthetic_demo | demo_label=UNUSUAL_TRANSACTION_CLUSTER. "
            "Demonstration pattern row seeded for MVP UI verification."
        ),
    },
]

DEMO_ATTRIBUTION_DISCLAIMER = (
    "DEMO DATA | synthetic_demo. This is a synthetic demonstration classification, "
    "not an assertion about the real owner of this address or about any real service."
)

DEMO_CASES: List[Dict[str, Any]] = [
    {
        "case_number": "CASE-DEMO-ETH-001",
        "title": "ETH Analysis - 0xf30ba1...",
        "wallet": "0xf30ba13e4b04Ce5dC4D254Ae5FA95477800F0EB0",
        "fraud_type": "investment_scam",
        "blockchain": "ethereum",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo ETH case 1",
        "tags": ["mvp-demo", "ethereum"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-BTC-001",
        "title": "BTC Analysis - bc1qgdjq...",
        "wallet": "bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv24sq90ecnvqqjwvw97",
        "fraud_type": "darknet",
        "blockchain": "bitcoin",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo BTC case 1",
        "tags": ["mvp-demo", "bitcoin"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-TRON-001",
        "title": "TRON Analysis - TAUN6Fwr...",
        "wallet": "TAUN6FwrnwwmaEqYcckffC7wYmbaS6cBiX",
        "fraud_type": "other",
        "blockchain": "tron",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo TRON case 1",
        "tags": ["mvp-demo", "tron"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-ETH-002",
        "title": "ETH Analysis - 0xd8dA6B...",
        "wallet": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        "fraud_type": "investment_scam",
        "blockchain": "ethereum",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo ETH case 2",
        "tags": ["mvp-demo", "ethereum"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-BTC-002",
        "title": "BTC Analysis - 34xp4vRo...",
        "wallet": "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo",
        "fraud_type": "darknet",
        "blockchain": "bitcoin",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo BTC case 2",
        "tags": ["mvp-demo", "bitcoin"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-TRON-002",
        "title": "TRON Analysis - TT2T17KZ...",
        "wallet": "TT2T17KZhoDu47i2E4FWxfG79zpe56sq8c",
        "fraud_type": "other",
        "blockchain": "tron",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo TRON case 2",
        "tags": ["mvp-demo", "tron"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-ETH-003",
        "title": "ETH Analysis - 0xBD612a...",
        "wallet": "0xBD612a3f30dcA67bF60a39Fd0D35e39B7aB80774",
        "fraud_type": "investment_scam",
        "blockchain": "ethereum",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo ETH case 3",
        "tags": ["mvp-demo", "ethereum"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-BTC-003",
        "title": "BTC Analysis - 1P5ZEDWT...",
        "wallet": "1P5ZEDWTKTFGxQjZphgWPQUpe554WKDfHQ",
        "fraud_type": "darknet",
        "blockchain": "bitcoin",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo BTC case 3",
        "tags": ["mvp-demo", "bitcoin"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-TRON-003",
        "title": "TRON Analysis - TXLAQ63X...",
        "wallet": "TXLAQ63Xg1NDyeVStL9vYk6hL6BvX9U7wW",
        "fraud_type": "other",
        "blockchain": "tron",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo TRON case 3",
        "tags": ["mvp-demo", "tron"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-ETH-004",
        "title": "ETH Analysis - 0x28C6c0...",
        "wallet": "0x28C6c06298d514Db089934071355E22Af164fC78",
        "fraud_type": "investment_scam",
        "blockchain": "ethereum",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo ETH case 4",
        "tags": ["mvp-demo", "ethereum"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-BTC-004",
        "title": "BTC Analysis - bc1qxy2k...",
        "wallet": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        "fraud_type": "darknet",
        "blockchain": "bitcoin",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo BTC case 4",
        "tags": ["mvp-demo", "bitcoin"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-TRON-004",
        "title": "TRON Analysis - TKW4y74k...",
        "wallet": "TKW4y74kXQf89Qj73eX8Z2H3x19S111wT6",
        "fraud_type": "other",
        "blockchain": "tron",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo TRON case 4",
        "tags": ["mvp-demo", "tron"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-ETH-005",
        "title": "ETH Analysis - 0x000000...",
        "wallet": "0x00000000219ab540356cBB839Cbe05303d7705Fa",
        "fraud_type": "investment_scam",
        "blockchain": "ethereum",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo ETH case 5",
        "tags": ["mvp-demo", "ethereum"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-BTC-005",
        "title": "BTC Analysis - 3FHNQ5k4...",
        "wallet": "3FHNQ5k4F4x3Y4JbMowXJd4A6K43ZKQJjQ",
        "fraud_type": "darknet",
        "blockchain": "bitcoin",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo BTC case 5",
        "tags": ["mvp-demo", "bitcoin"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-TRON-005",
        "title": "TRON Analysis - TDqSQfDX...",
        "wallet": "TDqSQfDXYG7rB58J8w3Z9Fz49XGzR327U7",
        "fraud_type": "other",
        "blockchain": "tron",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo TRON case 5",
        "tags": ["mvp-demo", "tron"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-ETH-006",
        "title": "ETH Analysis - 0xC02aaA...",
        "wallet": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "fraud_type": "investment_scam",
        "blockchain": "ethereum",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo ETH case 6",
        "tags": ["mvp-demo", "ethereum"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-BTC-006",
        "title": "BTC Analysis - bc1qw508...",
        "wallet": "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4",
        "fraud_type": "darknet",
        "blockchain": "bitcoin",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo BTC case 6",
        "tags": ["mvp-demo", "bitcoin"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-TRON-006",
        "title": "TRON Analysis - TLGqKkH8...",
        "wallet": "TLGqKkH89VbN1G45T3E9B71C8J7B9z6wT8",
        "fraud_type": "other",
        "blockchain": "tron",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo TRON case 6",
        "tags": ["mvp-demo", "tron"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-ETH-007",
        "title": "ETH Analysis - 0xBE0eB5...",
        "wallet": "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8",
        "fraud_type": "investment_scam",
        "blockchain": "ethereum",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo ETH case 7",
        "tags": ["mvp-demo", "ethereum"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-BTC-007",
        "title": "BTC Analysis - 1A1zP1eP...",
        "wallet": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        "fraud_type": "darknet",
        "blockchain": "bitcoin",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo BTC case 7",
        "tags": ["mvp-demo", "bitcoin"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-TRON-007",
        "title": "TRON Analysis - TSD2bH7F...",
        "wallet": "TSD2bH7F8Z1aY8Z3N9J3T7N9J9J3T7N9J9",
        "fraud_type": "other",
        "blockchain": "tron",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo TRON case 7",
        "tags": ["mvp-demo", "tron"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-ETH-008",
        "title": "ETH Analysis - 0xA0b869...",
        "wallet": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "fraud_type": "investment_scam",
        "blockchain": "ethereum",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo ETH case 8",
        "tags": ["mvp-demo", "ethereum"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-BTC-008",
        "title": "BTC Analysis - 3J98t1Wp...",
        "wallet": "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy",
        "fraud_type": "darknet",
        "blockchain": "bitcoin",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo BTC case 8",
        "tags": ["mvp-demo", "bitcoin"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-TRON-008",
        "title": "TRON Analysis - THY6P3F2...",
        "wallet": "THY6P3F2K9M6X7T3P9J3T7N9J9J3T7N9J9",
        "fraud_type": "other",
        "blockchain": "tron",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo TRON case 8",
        "tags": ["mvp-demo", "tron"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-ETH-009",
        "title": "ETH Analysis - 0x7a250d...",
        "wallet": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
        "fraud_type": "investment_scam",
        "blockchain": "ethereum",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo ETH case 9",
        "tags": ["mvp-demo", "ethereum"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-BTC-009",
        "title": "BTC Analysis - 1FeexV6b...",
        "wallet": "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF",
        "fraud_type": "darknet",
        "blockchain": "bitcoin",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo BTC case 9",
        "tags": ["mvp-demo", "bitcoin"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-TRON-009",
        "title": "TRON Analysis - TC1B4Y9X...",
        "wallet": "TC1B4Y9X5J9A2T7P8J3T7N9J9J3T7N9J9",
        "fraud_type": "other",
        "blockchain": "tron",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo TRON case 9",
        "tags": ["mvp-demo", "tron"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-ETH-010",
        "title": "ETH Analysis - 0x111111...",
        "wallet": "0x1111111254fb6c44bac0bed2854e76f90643097d",
        "fraud_type": "investment_scam",
        "blockchain": "ethereum",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo ETH case 10",
        "tags": ["mvp-demo", "ethereum"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-BTC-010",
        "title": "BTC Analysis - bc1qa5wk...",
        "wallet": "bc1qa5wkgaew2dkv56kfvj49j0av5nml45x9ek9hz6",
        "fraud_type": "darknet",
        "blockchain": "bitcoin",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo BTC case 10",
        "tags": ["mvp-demo", "bitcoin"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
    {
        "case_number": "CASE-DEMO-TRON-010",
        "title": "TRON Analysis - TP8A3B2F...",
        "wallet": "TP8A3B2F7H6N9P1J3T7N9J9J3T7N9J9",
        "fraud_type": "other",
        "blockchain": "tron",
        "direction": TransferDirection.OUTBOUND,
        "description": "Demo TRON case 10",
        "tags": ["mvp-demo", "tron"],
        "trace": {"max_hops": 1, "max_branches": 2, "max_pages_per_wallet": 1}
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def demo_header(**fields: Any) -> str:
    """Single-line JSON provenance header parsed by app.models.schemas."""
    payload: Dict[str, Any] = {"demo_data": True}
    payload.update(fields)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def demo_notes(spec: Dict[str, Any]) -> str:
    header = demo_header(
        case_type="MVP_DEMO",
        data_source="live_public_chain + synthetic_demo_metadata",
        subject_wallet=spec["wallet"],
        tags=spec.get("tags", []),
    )
    return f"{header}\n{spec['description']}"


def is_demo_case(case: Case) -> bool:
    notes = (case.investigator_notes or "").strip()
    if not notes.startswith("{"):
        return False
    try:
        parsed = json.loads(notes.splitlines()[0])
    except (ValueError, TypeError):
        return False
    return isinstance(parsed, dict) and parsed.get("demo_data") is True


def log(message: str) -> None:
    print(f"[seed] {message}", flush=True)


async def _existing_trace(db: AsyncSession, case_id: UUID) -> Optional[TraceRun]:
    result = await db.execute(
        select(TraceRun)
        .where(TraceRun.case_id == case_id, TraceRun.status.in_(["completed", "partial"]))
        .order_by(TraceRun.created_at.desc())
        .limit(1)
    )
    return result.scalars().first()


# ---------------------------------------------------------------------------
# Registry (Phases 5, 9)
# ---------------------------------------------------------------------------

async def _upsert_entity(db: AsyncSession, spec: Dict[str, Any], demo: bool) -> Entity:
    result = await db.execute(select(Entity).where(Entity.name == spec["name"]))
    entity = result.scalar_one_or_none()
    if entity is None:
        entity = Entity(
            entity_id=uuid.uuid4(),
            name=spec["name"],
            entity_type=spec["entity_type"],
            jurisdiction=spec.get("jurisdiction"),
            website=spec.get("website"),
            verification_level=spec.get("verification_level", "unverified"),
        )
        db.add(entity)
        await db.flush()

    for addr in spec.get("addresses", []):
        existing = await db.execute(
            select(EntityAddress).where(
                EntityAddress.blockchain == addr["blockchain"],
                EntityAddress.address == addr["address"].lower(),
            )
        )
        if existing.scalar_one_or_none() is not None:
            continue
        metadata = {"demo_data": True, "finding_source": DEMO_FINDING_SOURCE} if demo else {}
        db.add(
            EntityAddress(
                address_id=uuid.uuid4(),
                entity_id=entity.entity_id,
                blockchain=addr["blockchain"],
                address=addr["address"].lower(),
                label=addr["label"],
                category=addr.get("category"),
                source=DEMO_SOURCE if demo else addr["source"],
                source_url=addr.get("source_url"),
                confidence=Decimal(str(addr.get("confidence", 1.0))),
                metadata_=metadata,
            )
        )
    await db.flush()
    return entity


async def seed_registry(db: AsyncSession) -> None:
    if REAL_ENTITY_SEED.exists():
        catalogue = json.loads(REAL_ENTITY_SEED.read_text(encoding="utf-8"))
        for spec in catalogue:
            await _upsert_entity(db, spec, demo=False)
        log(f"real label registry loaded: {len(catalogue)} entities (Etherscan/OFAC sources)")
    else:
        log(f"WARNING: real entity seed not found at {REAL_ENTITY_SEED}; skipping")

    for spec in DEMO_ENTITIES:
        await _upsert_entity(db, spec, demo=True)
    log(f"synthetic DEMO label registry loaded: {len(DEMO_ENTITIES)} entities ({DEMO_SOURCE})")
    await db.commit()


# ---------------------------------------------------------------------------
# Cases (Phase 5)
# ---------------------------------------------------------------------------

async def get_or_create_case(
    db: AsyncSession, investigator: Investigator, spec: Dict[str, Any]
) -> Case:
    result = await db.execute(select(Case).where(Case.case_number == spec["case_number"]))
    case = result.scalar_one_or_none()
    if case is not None:
        log(f"{spec['case_number']}: already present ({case.case_id})")
        return case

    payload = CaseCreate(
        title=spec["title"],
        reported_wallet_address=spec["wallet"],
        blockchain=spec.get('blockchain', 'ethereum'),
        fraud_type=spec["fraud_type"],
        reported_asset="ETH",
        investigator_notes=demo_notes(spec),
    )
    case = await CaseService.create_case(db, payload, investigator.investigator_id)
    case.case_number = spec["case_number"]
    case.status = "under_investigation"
    await db.commit()
    await db.refresh(case)
    log(f"{spec['case_number']}: created ({case.case_id})")
    return case


# ---------------------------------------------------------------------------
# Live trace (Phases 5, 6, 7)
# ---------------------------------------------------------------------------

def build_adapters():
    from app.config import settings
    from app.services.blockchain import AlchemyProvider, EthereumAdapter
    from app.services.blockchain.adapter import BitcoinAdapter, TronAdapter

    from app.services.blockchain.providers.bitcoin import BlockstreamBitcoinProvider
    from app.services.blockchain.providers.tron import TronGridProvider

    api_key = settings.alchemy_api_key
    if not api_key:
        raise RuntimeError("ALCHEMY_API_KEY is not configured; cannot run live traces")
    return {
        "ethereum": EthereumAdapter(provider=AlchemyProvider(api_key=api_key, network=settings.alchemy_network)),
        "bitcoin": BitcoinAdapter(provider=BlockstreamBitcoinProvider()),
        "tron": TronAdapter(provider=TronGridProvider()),
    }


async def ensure_trace(
    db: AsyncSession, case: Case, spec: Dict[str, Any], skip_live: bool
) -> Optional[TraceRun]:
    existing = await _existing_trace(db, case.case_id)
    if existing is not None:
        log(f"{spec['case_number']}: trace already present ({existing.trace_id})")
        return existing

    if skip_live:
        log(f"{spec['case_number']}: --skip-live, mocking trace and graph")
        trace = TraceRun(
            trace_id=uuid.uuid4(),
            case_id=case.case_id,
            start_wallet_address=spec["wallet"].lower(),
            blockchain=spec.get("blockchain", "ethereum"),
            direction=spec.get("direction", "outbound").value if hasattr(spec.get("direction", "outbound"), "value") else str(spec.get("direction", "outbound")),
            max_hops=1,
            max_branches=2,
            min_amount=None,
            asset_filters=[],
            time_range_start=None,
            time_range_end=None,
            status="completed",
            result_status="success",
            provider="demo_mock",
            summary={"wallet_count": 3, "transaction_count": 2, "edge_count": 2},
            parameters={},
            errors=[]
        )
        db.add(trace)
        
        graph_payload = {
            "root_wallet_address": spec["wallet"].lower(),
            "blockchain": spec.get("blockchain", "ethereum"),
            "node_count": 3,
            "edge_count": 2,
            "max_hop_depth": 1,
            "nodes": [
                {"id": spec["wallet"].lower(), "type": "wallet", "hop": 0, "metadata": {"root": True}},
                {"id": _demo_address("de10"), "type": "wallet", "hop": 1, "metadata": {}},
                {"id": _demo_address("de11"), "type": "wallet", "hop": 1, "metadata": {}}
            ],
            "edges": [
                {"id": "mockedge1", "source": spec["wallet"].lower(), "target": _demo_address("de10"), "type": "transferred_to", "transaction_hash": "0xabc", "amount": "100000", "hop": 1},
                {"id": "mockedge2", "source": spec["wallet"].lower(), "target": _demo_address("de11"), "type": "transferred_to", "transaction_hash": "0xdef", "amount": "50000", "hop": 1}
            ]
        }
        db.add(
            GraphRecord(
                case_id=case.case_id,
                trace_id=trace.trace_id,
                root_wallet_address=spec["wallet"].lower(),
                blockchain=spec.get("blockchain", "ethereum"),
                max_hop_depth=1,
                branch_limit=2,
                dust_threshold=None,
                time_window_start=None,
                time_window_end=None,
                node_count=3,
                edge_count=2,
                graph_data=graph_payload,
            )
        )
        
        await db.flush()
        return trace

    cfg_kwargs = dict(spec.get("trace", {}))
    config = TraceConfig(
        max_hops=cfg_kwargs.get("max_hops", 1),
        max_branches=cfg_kwargs.get("max_branches", 3),
        max_pages_per_wallet=cfg_kwargs.get("max_pages_per_wallet", 1),
        page_size=100,
    )
    service = TraceService(build_adapters())
    log(
        f"{spec['case_number']}: running live trace "
        f"(hops={config.max_hops}, branches={config.max_branches}, "
        f"pages/wallet={config.max_pages_per_wallet})"
    )
    trace = await service.execute_trace(
        db, case, start_wallet=spec["wallet"], direction=spec["direction"], config=config
    )
    log(
        f"{spec['case_number']}: trace {trace.status} "
        f"({trace.result_status}, txs stored via provider={trace.provider})"
    )
    return trace


# ---------------------------------------------------------------------------
# Derived analytics (Phases 7, 8, 9, 10)
# ---------------------------------------------------------------------------

async def load_graph(db: AsyncSession, trace_id: UUID) -> Optional[CanonicalGraph]:
    result = await db.execute(select(GraphRecord).where(GraphRecord.trace_id == trace_id))
    record = result.scalar_one_or_none()
    if record is None:
        return None
    return CanonicalGraph.model_validate(record.graph_data)


async def _has_real_patterns(db: AsyncSession, trace_id: UUID) -> bool:
    """True when a non-demo pattern row already exists for this trace."""
    result = await db.execute(
        select(PatternRecord.pattern_id)
        .where(
            PatternRecord.trace_id == trace_id,
            PatternRecord.description.notilike("DEMO DATA |%"),
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def derive_real_patterns(
    db: AsyncSession, case: Case, trace: TraceRun, graph: CanonicalGraph
) -> int:
    findings = run_all_detectors(graph)
    if not findings:
        log(f"real pattern detectors: 0 findings for trace {trace.trace_id}")
        return 0
    records = await persist_findings(db, findings, case.case_id, trace.trace_id)
    await db.flush()
    log(f"real pattern detectors: {len(records)} findings persisted (LIVE ON-CHAIN derived)")
    return len(records)


async def derive_real_attributions(
    db: AsyncSession, case: Case, trace: TraceRun, graph: CanonicalGraph
) -> int:
    engine = AttributionEngine(db)
    persisted = 0
    for node in graph.nodes:
        address = node.id.lower()
        existing = await db.execute(
            select(VaspAttributionRecord.attribution_id).where(
                VaspAttributionRecord.trace_id == trace.trace_id,
                VaspAttributionRecord.wallet_address == address,
            ).limit(1)
        )
        if existing.scalar_one_or_none() is not None:
            continue
        attribution = await engine.attribute_address(
            address, graph.blockchain, case.case_id, trace.trace_id
        )
        if attribution is None:
            continue
        evidence = dict(attribution.evidence or {})
        evidence["demo_data"] = evidence.get("source") == DEMO_SOURCE
        attribution.evidence = evidence
        await engine.persist_attribution(attribution)
        persisted += 1
    await db.flush()
    if persisted:
        log(f"registry attributions persisted: {persisted} (real label + demo labels)")
    return persisted


async def add_demo_patterns(
    db: AsyncSession, case: Case, trace: TraceRun, graph: CanonicalGraph
) -> int:
    if not graph.nodes:
        return 0
    root = graph.root_wallet_address.lower()
    added = 0
    for spec in DEMO_PATTERNS:
        existing = await db.execute(
            select(PatternRecord.pattern_id).where(
                PatternRecord.trace_id == trace.trace_id,
                PatternRecord.wallet_address == root,
                PatternRecord.pattern_type == spec["pattern_type"],
            ).limit(1)
        )
        if existing.scalar_one_or_none() is not None:
            continue
        db.add(
            PatternRecord(
                pattern_id=uuid.uuid4(),
                case_id=case.case_id,
                trace_id=trace.trace_id,
                wallet_address=root,
                pattern_type=spec["pattern_type"],
                confidence=Decimal("0.70"),
                description=spec["description"],
                evidence={
                    "demo_data": True,
                    "finding_source": DEMO_FINDING_SOURCE,
                    "demo_label": spec["demo_label"],
                    "graph_source": "live_on_chain_derived",
                    "wallet_addresses": [root],
                    "disclaimer": "Synthetic DEMO DATA pattern row for MVP demonstration.",
                },
                metrics={
                    "demo_data": True,
                    "finding_source": DEMO_FINDING_SOURCE,
                    "demo_label": spec["demo_label"],
                    "node_count": graph.node_count,
                    "edge_count": graph.edge_count,
                    "max_hop_depth": graph.max_hop_depth,
                },
            )
        )
        added += 1
    await db.flush()
    if added:
        log(f"synthetic DEMO pattern rows added: {added}")
    return added


async def add_demo_attributions(
    db: AsyncSession, case: Case, trace: TraceRun, graph: CanonicalGraph
) -> int:
    counterparties = [
        n.id.lower() for n in graph.nodes if n.id.lower() != graph.root_wallet_address.lower()
    ]
    if not counterparties:
        log("synthetic DEMO attributions: no counterparties in graph, skipped")
        return 0

    demo_entities = list(
        (
            await db.execute(
                select(Entity).where(Entity.name.in_([e["name"] for e in DEMO_ENTITIES]))
            )
        ).scalars()
    )
    if not demo_entities:
        return 0

    attributed = await db.execute(
        select(VaspAttributionRecord.wallet_address).where(
            VaspAttributionRecord.trace_id == trace.trace_id
        )
    )
    already = {row[0] for row in attributed.all()}

    added = 0
    for index, address in enumerate(counterparties[: len(demo_entities)]):
        if address in already:
            continue
        entity = demo_entities[index % len(demo_entities)]
        db.add(
            VaspAttributionRecord(
                attribution_id=uuid.uuid4(),
                case_id=case.case_id,
                trace_id=trace.trace_id,
                wallet_address=address,
                candidate_entity_id=entity.entity_id,
                candidate_entity=entity,
                provenance_level="INFERRED",
                confidence=Decimal("0.40"),
                attribution_method="multi_signal",
                evidence={
                    "demo_data": True,
                    "finding_source": DEMO_FINDING_SOURCE,
                    "address": address,
                    "blockchain": graph.blockchain,
                    "entity_id": str(entity.entity_id),
                    "entity_name": entity.name,
                    "label": "DEMO label (synthetic)",
                    "source": DEMO_SOURCE,
                    "confidence": 0.40,
                    "disclaimer": DEMO_ATTRIBUTION_DISCLAIMER,
                },
                source=DEMO_SOURCE,
            )
        )
        added += 1
    await db.flush()
    if added:
        log(f"synthetic DEMO attribution rows added: {added}")
    return added


async def calculate_risk(db: AsyncSession, case: Case, trace: TraceRun, graph: CanonicalGraph) -> int:
    existing = await db.execute(
        select(RiskScoreRecord.risk_score_id)
        .where(RiskScoreRecord.trace_id == trace.trace_id)
        .limit(1)
    )
    if existing.scalar_one_or_none() is not None:
        log("risk scores already present for trace; skipped")
        return 0

    engine = RiskEngine(db)
    scores = await engine.calculate_all_wallets(case.case_id, trace.trace_id, graph)
    await db.flush()
    log(f"risk scores computed from real graph: {len(scores)} wallets")
    return len(scores)


async def add_demo_evidence(db: AsyncSession, case: Case, trace: TraceRun) -> int:
    result = await db.execute(
        select(Evidence.evidence_id).where(Evidence.case_id == case.case_id).limit(1)
    )
    if result.scalar_one_or_none() is not None:
        return 0

    tx_result = await db.execute(
        select(GraphRecord).where(GraphRecord.trace_id == trace.trace_id)
    )
    graph_record = tx_result.scalar_one_or_none()

    entries = [
        {
            "type": "note",
            "reference_id": case.case_id,
            "note": (
                "[DEMO DATA] demo_data=true | finding_source=synthetic_demo - "
                "Case framing and investigation narrative are demonstration content "
                "created for the MVP walkthrough."
            ),
        },
        {
            "type": "wallet",
            "reference_id": trace.trace_id,
            "note": (
                "[DEMO DATA] demo_data=false | finding_source=live_on_chain - "
                f"Subject wallet {case.reported_wallet_address} was traced against "
                f"Ethereum Mainnet via provider {trace.provider}; graph "
                f"{graph_record.node_count if graph_record else 0} nodes / "
                f"{graph_record.edge_count if graph_record else 0} edges."
            ),
        },
        {
            "type": "pattern",
            "reference_id": trace.trace_id,
            "note": (
                "[DEMO DATA] demo_data=true | finding_source=synthetic_demo - "
                "Pattern rows tagged demo_data=true are seeded demonstration findings; "
                "pattern rows without that marker were derived from the live trace graph."
            ),
        },
    ]

    count = 0
    for entry in entries:
        db.add(
            Evidence(
                evidence_id=uuid.uuid4(),
                case_id=case.case_id,
                evidence_type=entry["type"],
                reference_id=entry["reference_id"],
                investigator_note=entry["note"],
                investigator_id=case.investigator_id,
            )
        )
        count += 1
    await db.flush()
    log(f"evidence rows added: {count}")
    return count


async def generate_report(
    db: AsyncSession, case: Case, investigator: Investigator, spec: Dict[str, Any]
) -> Optional[str]:
    store = ReportStore(db)
    generator = ReportGenerator(db)

    existing = await store.get_reports_for_case(case.case_id)
    if existing:
        log(f"{spec['case_number']}: {len(existing)} report(s) already present; skipped")
        return None

    job = await store.create_job(
        case.case_id, "detailed", "json", investigator.investigator_id,
        extra_parameters={"demo_data": True, "finding_source": DEMO_FINDING_SOURCE},
    )
    await store.mark_job_started(job)
    report = await generator.generate(
        case.case_id, "detailed", "json", generated_by=investigator.investigator_id
    )
    record = await store.save_report(report, investigator.investigator_id)
    await store.mark_job_completed(job, result={"report_id": str(record.report_id)})
    await db.commit()
    log(f"{spec['case_number']}: report {record.report_id} generated (json/detailed)")
    return str(record.report_id)


# ---------------------------------------------------------------------------
# Reset (Phase 19)
# ---------------------------------------------------------------------------

async def recalc_risk(db: AsyncSession) -> None:
    """Drop derived risk rows for seeded demo traces so they can be recomputed."""
    demo_cases = [
        c
        for c in (await db.execute(select(Case).where(Case.investigator_notes.is_not(None)))).scalars()
        if is_demo_case(c)
    ]
    if not demo_cases:
        return
    trace_ids = [
        t.trace_id
        for t in (await db.execute(select(TraceRun).where(TraceRun.case_id.in_([c.case_id for c in demo_cases])))).scalars()
    ]
    if not trace_ids:
        return
    await db.execute(sa_delete(RiskScoreRecord).where(RiskScoreRecord.trace_id.in_(trace_ids)))
    case_ids = [c.case_id for c in demo_cases]
    await db.execute(sa_delete(ReportRecord).where(ReportRecord.case_id.in_(case_ids)))
    await db.execute(sa_delete(JobRecord).where(JobRecord.case_id.in_(case_ids)))
    await db.commit()
    log(
        f"recalc: dropped derived risk rows for {len(trace_ids)} demo trace(s) "
        f"and {len(case_ids)} report(s) so both are rebuilt"
    )


async def reset_demo(db: AsyncSession) -> None:
    """Remove previously seeded demo rows using the schema's ON DELETE CASCADE rules."""
    cases = (
        (await db.execute(select(Case).where(Case.investigator_notes.is_not(None))))
        .scalars()
        .all()
    )
    demo_case_ids = [c.case_id for c in cases if is_demo_case(c)]
    if demo_case_ids:
        await db.execute(sa_delete(Case).where(Case.case_id.in_(demo_case_ids)))

    demo_names = [spec["name"] for spec in DEMO_ENTITIES]
    entities = (
        (await db.execute(select(Entity).where(Entity.name.in_(demo_names)))).scalars().all()
    )
    if entities:
        await db.execute(sa_delete(Entity).where(Entity.entity_id.in_([e.entity_id for e in entities])))

    await db.commit()
    log(f"reset complete: {len(demo_case_ids)} demo case(s), {len(entities)} demo entity(ies)")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

async def run(args: argparse.Namespace) -> int:
    async with async_session_maker() as db:
        if args.reset:
            await reset_demo(db)
        elif args.recalc_risk:
            await recalc_risk(db)

        result = await db.execute(
            select(Investigator).where(Investigator.username == args.username)
        )
        investigator = result.scalar_one_or_none()
        if investigator is None:
            log(f"ERROR: investigator '{args.username}' not found.")
            log("Run scripts/create_investigator.py first (Phase 1).")
            return 1

        await seed_registry(db)

        summary: Dict[str, Dict[str, Any]] = {}
        for spec in DEMO_CASES:
            stats = {"trace": "skipped", "patterns": 0, "attributions": 0, "risk": 0, "evidence": 0}
            case = await get_or_create_case(db, investigator, spec)

            trace = await ensure_trace(db, case, spec, args.skip_live)
            if trace is None or trace.status not in ("completed", "partial"):
                stats["trace"] = trace.status if trace else "none"
                summary[spec["case_number"]] = stats
                continue

            graph = await load_graph(db, trace.trace_id)
            if graph is None:
                log(f"{spec['case_number']}: no graph persisted for trace")
                stats["trace"] = "no_graph"
                summary[spec["case_number"]] = stats
                continue

            stats["trace"] = trace.status
            log(
                f"{spec['case_number']}: graph {graph.node_count} nodes / "
                f"{graph.edge_count} edges (LIVE ON-CHAIN)"
            )

            if not await _has_real_patterns(db, trace.trace_id):
                stats["patterns"] = await derive_real_patterns(db, case, trace, graph)
            stats["attributions"] += await derive_real_attributions(db, case, trace, graph)
            stats["risk"] = await calculate_risk(db, case, trace, graph)
            await db.commit()

            stats["patterns"] += await add_demo_patterns(db, case, trace, graph)
            stats["attributions"] += await add_demo_attributions(db, case, trace, graph)
            stats["evidence"] = await add_demo_evidence(db, case, trace)
            await db.commit()

            if not args.skip_reports:
                await generate_report(db, case, investigator, spec)

            summary[spec["case_number"]] = stats

        log("--- summary ---")
        for number, stats in summary.items():
            log(f"{number}: {json.dumps(stats, sort_keys=True)}")
        log("done. Demo rows carry demo_data markers; live rows are provider-derived.")
        return 0


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed LedgerLens MVP demo data")
    parser.add_argument("--username", default=DEFAULT_INVESTIGATOR_USERNAME)
    parser.add_argument("--reset", action="store_true", help="delete previously seeded demo rows")
    parser.add_argument("--skip-live", action="store_true", help="do not call the chain provider")
    parser.add_argument("--skip-reports", action="store_true", help="do not generate reports")
    parser.add_argument(
        "--recalc-risk",
        action="store_true",
        help="drop derived risk rows for seeded demo traces and recompute them",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
