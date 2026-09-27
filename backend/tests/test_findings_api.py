"""MVP findings API tests — GET /cases/{id}/patterns|evidence|attributions.

Verifies the documented read contracts plus the demo/live provenance flags the
UI relies on: synthetic demonstration rows must serialize with demo_data=true
and finding_source="demo"; rows derived from a live trace serialize with
demo_data=false.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, List
from uuid import UUID, uuid4

from httpx import AsyncClient

from app.api.v1.cases import MOCK_INVESTIGATOR_ID
from app.db.database import get_db
from app.db.models import Case, Entity, Evidence, PatternRecord, VaspAttributionRecord
from app.main import app

CASE_ID = uuid4()
TRACE_ID = uuid4()
OVERRIDE_KEYS = (get_db,)

DEMO_PATTERN_ID = uuid4()
LIVE_PATTERN_ID = uuid4()
DEMO_EVIDENCE_ID = uuid4()
LIVE_EVIDENCE_ID = uuid4()
DEMO_ATTRIBUTION_ID = uuid4()
LIVE_ATTRIBUTION_ID = uuid4()


def make_case() -> Case:
    return Case(
        case_id=CASE_ID,
        case_number="LL-FIND-001",
        title="Findings API fixture case",
        reported_wallet_address="0x" + "2" * 40,
        blockchain="ethereum",
        fraud_type="investment_scam",
        investigator_id=MOCK_INVESTIGATOR_ID,
        status="active",
        created_at=datetime(2026, 9, 22, tzinfo=timezone.utc),
    )


def make_demo_pattern(case: Case) -> PatternRecord:
    return PatternRecord(
        pattern_id=DEMO_PATTERN_ID,
        case_id=case.case_id,
        trace_id=TRACE_ID,
        wallet_address="0x" + "2" * 40,
        pattern_type="rapid_forwarding",
        confidence=Decimal("0.70"),
        description="DEMO DATA | synthetic_demo | demo_label=HIGH_TRANSACTION_VELOCITY",
        evidence={"demo_data": True, "demo_label": "HIGH_TRANSACTION_VELOCITY"},
        metrics={"demo_data": True, "demo_label": "HIGH_TRANSACTION_VELOCITY"},
        detected_at=datetime(2026, 9, 23, tzinfo=timezone.utc),
    )


def make_live_pattern(case: Case) -> PatternRecord:
    return PatternRecord(
        pattern_id=LIVE_PATTERN_ID,
        case_id=case.case_id,
        trace_id=TRACE_ID,
        wallet_address="0x" + "3" * 40,
        pattern_type="fan_out",
        confidence=Decimal("0.90"),
        description="Fan-out to 12 counterparties within 2 hops (live trace derived)",
        evidence={"wallet_addresses": ["0x" + "3" * 40]},
        metrics={"node_count": 14},
        detected_at=datetime(2026, 9, 23, tzinfo=timezone.utc),
    )


def make_demo_evidence(case: Case) -> Evidence:
    return Evidence(
        evidence_id=DEMO_EVIDENCE_ID,
        case_id=case.case_id,
        evidence_type="note",
        reference_id=case.case_id,
        investigator_note="[DEMO DATA] demo_data=true | synthetic analyst note",
        investigator_id=case.investigator_id,
        pinned_at=datetime(2026, 9, 23, tzinfo=timezone.utc),
    )


def make_live_evidence(case: Case) -> Evidence:
    return Evidence(
        evidence_id=LIVE_EVIDENCE_ID,
        case_id=case.case_id,
        evidence_type="wallet",
        reference_id=TRACE_ID,
        investigator_note="[LIVE] demo_data=false | subject traced via Alchemy",
        investigator_id=case.investigator_id,
        pinned_at=datetime(2026, 9, 23, tzinfo=timezone.utc),
    )


def make_entity(name: str) -> Entity:
    return Entity(
        entity_id=uuid4(),
        name=name,
        entity_type="exchange",
        verification_level="unverified",
    )


def make_attribution(case: Case, entity: Entity, demo: bool) -> VaspAttributionRecord:
    return VaspAttributionRecord(
        attribution_id=DEMO_ATTRIBUTION_ID if demo else LIVE_ATTRIBUTION_ID,
        case_id=case.case_id,
        trace_id=TRACE_ID,
        wallet_address="0x" + "4" * 40,
        candidate_entity_id=entity.entity_id,
        candidate_entity=entity,
        provenance_level="INFERRED" if demo else "DIRECT",
        confidence=Decimal("0.40") if demo else Decimal("0.95"),
        attribution_method="multi_signal" if demo else "registry_exact_match",
        evidence={
            "demo_data": demo,
            "disclaimer": "synthetic demonstration classification" if demo else None,
        },
        source="demo_seed" if demo else "etherscan",
        attributed_at=datetime(2026, 9, 23, tzinfo=timezone.utc),
    )


class FakeFindingsDB:
    """Session double answering CaseService.get_case and the three listings."""

    def __init__(self, case: Case, rows: List[Any]) -> None:
        self.case = case
        self.rows = rows

    async def execute(self, stmt, *args, **kwargs):
        descriptions = stmt.column_descriptions
        target = descriptions[0]["type"] if descriptions else None
        matched = [r for r in self.rows if isinstance(r, target)] if target else []

        class _Result:
            def __init__(self, items: List[Any]) -> None:
                self._items = items

            def scalar_one_or_none(self_inner):
                return self_inner._items[0] if self_inner._items else None

            def scalars(self_inner):
                return self_inner

            def all(self_inner):
                return self_inner._items

        if target is Case:
            return _Result([self.case] if self.case else [])
        return _Result(matched)


async def _setup(db_rows: List[Any], case: Case | None = None) -> None:
    if case is None:
        case = next((r for r in db_rows if isinstance(r, Case)), None)
    resolved = case
    for key in OVERRIDE_KEYS:
        app.dependency_overrides[key] = lambda: FakeFindingsDB(resolved, db_rows)


async def _teardown() -> None:
    for key in OVERRIDE_KEYS:
        app.dependency_overrides.pop(key, None)


async def test_patterns_endpoint_flags_demo_and_live_rows():
    case = make_case()
    await _setup([case, make_demo_pattern(case), make_live_pattern(case)])
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.get(f"/api/v1/cases/{CASE_ID}/patterns")
        assert r.status_code == 200
        patterns = r.json()["patterns"]
        assert len(patterns) == 2
        by_id = {p["pattern_id"]: p for p in patterns}
        demo = by_id[str(DEMO_PATTERN_ID)]
        assert demo["demo_data"] is True
        assert demo["finding_source"] == "demo"
        assert demo["demo_label"] == "HIGH_TRANSACTION_VELOCITY"
        live = by_id[str(LIVE_PATTERN_ID)]
        assert live["demo_data"] is False
        assert live["finding_source"] == "live_trace_derived"
    finally:
        await _teardown()


async def test_evidence_endpoint_flags_demo_and_live_rows():
    case = make_case()
    await _setup([case, make_demo_evidence(case), make_live_evidence(case)])
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.get(f"/api/v1/cases/{CASE_ID}/evidence")
        assert r.status_code == 200
        evidence = r.json()["evidence"]
        assert len(evidence) == 2
        by_id = {e["evidence_id"]: e for e in evidence}
        assert by_id[str(DEMO_EVIDENCE_ID)]["demo_data"] is True
        assert by_id[str(DEMO_EVIDENCE_ID)]["finding_source"] == "demo"
        assert by_id[str(LIVE_EVIDENCE_ID)]["demo_data"] is False
        assert by_id[str(LIVE_EVIDENCE_ID)]["finding_source"] == "live_on_chain"
    finally:
        await _teardown()


async def test_attributions_endpoint_flags_demo_and_registry_rows():
    case = make_case()
    demo_entity = make_entity("DEMO_EXCHANGE_A")
    live_entity = make_entity("Etherscan-verified label")
    await _setup(
        [
            case,
            make_attribution(case, demo_entity, demo=True),
            make_attribution(case, live_entity, demo=False),
        ]
    )
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.get(f"/api/v1/cases/{CASE_ID}/attributions")
        assert r.status_code == 200
        attributions = r.json()["attributions"]
        assert len(attributions) == 2
        by_id = {a["attribution_id"]: a for a in attributions}
        demo = by_id[str(DEMO_ATTRIBUTION_ID)]
        assert demo["demo_data"] is True
        assert demo["finding_source"] == "demo"
        assert demo["entity_name"] == "DEMO_EXCHANGE_A"
        assert demo["disclaimer"]
        live = by_id[str(LIVE_ATTRIBUTION_ID)]
        assert live["demo_data"] is False
        assert live["finding_source"] == "registry_label"
        assert live["entity_name"] == "Etherscan-verified label"
    finally:
        await _teardown()


async def test_findings_endpoints_404_for_missing_case():
    await _setup([])
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            missing = uuid4()
            for path in ("patterns", "evidence", "attributions"):
                r = await client.get(f"/api/v1/cases/{missing}/{path}")
                assert r.status_code == 404
                assert r.json()["detail"]["error"]["code"] == "CASE_NOT_FOUND"
    finally:
        await _teardown()
