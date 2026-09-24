"""Phase 6 Step 2 — focused evidence/report aggregation tests.

Covers the Step 2 contract only:
- Evidence store provisioning per docs/DATA_MODEL.md section 4.11
- Evidence section aggregation with chain-of-custody provenance
- Explicit representation of unavailable evidence/notes (no fabrication)
- Reuse of the existing case-level investigator notes record
- Deterministic output and compatibility with the Step 1 generator contract
"""

import json
import re
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import pytest

from app.db.models import Evidence
from app.services.ai.grounding import GroundingLayer
from app.services.reporting import (
    REPORT_TYPE_SECTIONS,
    SECTION_ORDER,
    InvalidReportTypeError,
    ReportCaseNotFoundError,
    ReportGenerator,
)

FIXED_TS = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)

CASE_ID = uuid4()
INVESTIGATOR_ID = uuid4()
EVIDENCE_ID_LATE = uuid4()
EVIDENCE_ID_EARLY = uuid4()
EVIDENCE_REF_TX = uuid4()
EVIDENCE_REF_PATTERN = uuid4()
PATTERN_ID = uuid4()
ATTRIBUTION_ID = uuid4()
RISK_SCORE_ID = uuid4()
TRACE_ID = uuid4()

WALLET = "0x" + "1" * 40
MID = "0x" + "2" * 40
DEST = "0x" + "3" * 40
TX_HASH_1 = "0x" + "a" * 64
TX_HASH_2 = "0x" + "b" * 64

CASE: Dict[str, Any] = {
    # Mirrors GroundingLayer.get_case, which returns case_id as str.
    "case_id": str(CASE_ID),
    "case_number": "LL-2026-0001",
    "title": "Step 2 aggregation fixture case",
    "reported_wallet_address": WALLET,
    "reported_transaction_hash": TX_HASH_1,
    "blockchain": "ethereum",
    "fraud_type": "investment_scam",
    "status": "active",
    "reported_amount": "5.0",
    "reported_asset": "ETH",
    "reported_date": "2026-09-20T00:00:00+00:00",
    "created_at": "2026-09-21T00:00:00+00:00",
    "updated_at": "2026-09-22T00:00:00+00:00",
    "investigator_notes": "Victim reported loss after fake investment platform",
    "investigator_id": INVESTIGATOR_ID,
}

TRACE_RUNS: List[Dict[str, Any]] = [
    {
        "trace_id": str(TRACE_ID),
        "start_wallet_address": WALLET,
        "blockchain": "ethereum",
        "direction": "outbound",
        "max_hops": 3,
        "max_branches": 25,
        "status": "completed",
        "result_status": "complete",
        "created_at": "2026-09-22T10:00:00+00:00",
        "completed_at": "2026-09-22T10:05:00+00:00",
    }
]

TRANSACTIONS: List[Dict[str, Any]] = [
    {
        "transaction_hash": TX_HASH_1,
        "block_number": 100,
        "block_timestamp": "2026-09-22T11:00:00+00:00",
        "from_address": WALLET,
        "to_address": MID,
        "amount": "1.0",
        "asset_symbol": "ETH",
        "transaction_type": "outbound",
        "status": "confirmed",
        "discovered_at_hop": 1,
    },
    {
        "transaction_hash": TX_HASH_2,
        "block_number": 105,
        "block_timestamp": "2026-09-22T12:00:00+00:00",
        "from_address": MID,
        "to_address": DEST,
        "amount": "2.0",
        "asset_symbol": "ETH",
        "transaction_type": "outbound",
        "status": "confirmed",
        "discovered_at_hop": 2,
    },
]

ATTRIBUTIONS: List[Dict[str, Any]] = [
    {
        "attribution_id": str(ATTRIBUTION_ID),
        "case_id": str(CASE_ID),
        "wallet_address": DEST,
        "entity": "ExampleExchange",
        "provenance_level": "cluster",
        "confidence": "0.85",
        "attribution_method": "address_clustering",
        "source": "curated_registry",
        "attributed_at": "2026-09-23T00:00:00+00:00",
        "evidence": {"source": "internal"},
    }
]

RISK_SCORES: List[Dict[str, Any]] = [
    {
        "risk_score_id": str(RISK_SCORE_ID),
        "wallet_address": MID,
        "score": 62,
        "risk_category": "high",
        "scoring_version": "v1.0.0",
        "calculated_at": "2026-09-23T06:00:00+00:00",
        "factors": [
            {
                "factor": "rapid_forwarding",
                "weight": "0.50",
                "contribution": 31,
                "evidence": [],
                "explanation": "Funds forwarded within two hops",
            }
        ],
    }
]

PATTERNS: List[Dict[str, Any]] = [
    {
        "pattern_id": str(PATTERN_ID),
        "pattern_type": "rapid_movement",
        "wallet_address": MID,
        "confidence": "0.90",
        "description": "Funds forwarded within two hops",
        "evidence": {"transaction_hashes": [TX_HASH_1]},
        "detected_at": "2026-09-23T07:00:00+00:00",
    }
]

EVIDENCE: List[Dict[str, Any]] = [
    {
        "evidence_id": str(EVIDENCE_ID_LATE),
        "evidence_type": "transaction",
        "reference_id": str(EVIDENCE_REF_TX),
        "investigator_note": "Key outflow to intermediary",
        "investigator_id": str(INVESTIGATOR_ID),
        "pinned_at": "2026-09-24T10:00:00+00:00",
    },
    {
        "evidence_id": str(EVIDENCE_ID_EARLY),
        "evidence_type": "pattern",
        "reference_id": str(EVIDENCE_REF_PATTERN),
        "investigator_note": "Pattern corroborates rapid forwarding",
        "investigator_id": str(INVESTIGATOR_ID),
        "pinned_at": "2026-09-23T09:00:00+00:00",
    },
]


class StubGrounding:
    """Grounding double returning fixed fixture data for aggregation tests."""

    _MISSING = object()

    def __init__(
        self,
        case: Any = _MISSING,
        evidence: Any = _MISSING,
        evidence_error: Optional[BaseException] = None,
    ) -> None:
        self.case = CASE if case is self._MISSING else case
        self.evidence = EVIDENCE if evidence is self._MISSING else evidence
        self.evidence_error = evidence_error

    async def get_case(self, case_id: UUID):
        return self.case

    async def get_trace_runs(self, case_id: UUID):
        return list(TRACE_RUNS)

    async def get_graph(self, case_id: UUID, trace_id=None):
        return None

    async def get_patterns(self, case_id: UUID, trace_id=None, wallet_address=None):
        return list(PATTERNS)

    async def get_attributions(self, case_id: UUID, trace_id=None, wallet_address=None):
        return list(ATTRIBUTIONS)

    async def get_risk_scores(self, case_id: UUID, trace_id=None, wallet_address=None):
        return list(RISK_SCORES)

    async def get_transactions(self, case_id: UUID, trace_id=None, limit: int = 100):
        return list(TRANSACTIONS)

    async def get_evidence(self, case_id: UUID):
        if self.evidence_error is not None:
            raise self.evidence_error
        return list(self.evidence)


def make_generator(**stub_kwargs: Any) -> ReportGenerator:
    generator = ReportGenerator(None)
    generator.grounding = StubGrounding(**stub_kwargs)
    return generator


def section(report: Dict[str, Any], key: str) -> Dict[str, Any]:
    return next(s for s in report["sections"] if s["key"] == key)


class TestEvidenceProvisioning:
    """Evidence model must match docs/DATA_MODEL.md section 4.11."""

    def test_evidence_model_matches_data_model(self):
        assert Evidence.__tablename__ == "evidence"
        columns = Evidence.__table__.columns
        expected = {
            "evidence_id",
            "case_id",
            "evidence_type",
            "reference_id",
            "investigator_note",
            "investigator_id",
            "pinned_at",
        }
        assert set(columns.keys()) == expected
        assert columns["evidence_id"].primary_key is True
        assert columns["case_id"].nullable is False
        assert columns["evidence_type"].nullable is False
        assert columns["reference_id"].nullable is False
        assert columns["investigator_note"].nullable is True
        assert columns["investigator_id"].nullable is False

    async def test_grounding_get_evidence_returns_chain_of_custody_fields(self):
        row = SimpleNamespace(
            evidence_id=uuid4(),
            evidence_type="transaction",
            reference_id=uuid4(),
            investigator_note="Pinned during review",
            investigator_id=uuid4(),
            pinned_at=datetime(2026, 9, 24, 10, 0, 0, tzinfo=timezone.utc),
        )

        class _Result:
            def scalars(self_inner):
                return self_inner

            def all(self_inner):
                return [row]

        class _DB:
            async def execute(self, _query):
                return _Result()

        result = await GroundingLayer(_DB()).get_evidence(CASE_ID)

        assert len(result) == 1
        item = result[0]
        assert item["evidence_id"] == str(row.evidence_id)
        assert item["reference_id"] == str(row.reference_id)
        assert item["investigator_id"] == str(row.investigator_id)
        assert item["investigator_note"] == row.investigator_note
        assert item["pinned_at"] == row.pinned_at.isoformat()


class TestEvidenceAggregation:
    async def test_evidence_section_aggregates_with_provenance(self):
        report = await make_generator().generate(
            CASE_ID, "detailed", generated_at=FIXED_TS
        )
        evidence_section = section(report, "evidence_references")

        assert evidence_section["available"] is True
        assert evidence_section["data"]["count"] == 2
        items = evidence_section["data"]["evidence"]
        assert {i["reference_id"] for i in items} == {
            str(EVIDENCE_REF_TX),
            str(EVIDENCE_REF_PATTERN),
        }
        for item in items:
            assert item["evidence_id"]
            assert item["investigator_id"] == str(INVESTIGATOR_ID)
            assert item["pinned_at"]
        # Deterministic ordering: earliest pinned_at first.
        assert [i["evidence_id"] for i in items] == [
            str(EVIDENCE_ID_EARLY),
            str(EVIDENCE_ID_LATE),
        ]

    async def test_evidence_store_failure_is_explicitly_unavailable(self):
        report = await make_generator(
            evidence_error=RuntimeError("relation does not exist")
        ).generate(CASE_ID, "detailed", generated_at=FIXED_TS)

        evidence_section = section(report, "evidence_references")
        assert evidence_section["available"] is False
        assert evidence_section["data"] is None
        assert "Evidence store unavailable" in evidence_section["reason"]
        assert "evidence_references" in report["unavailable_sections"]
        # Unavailability is scoped: other sources still aggregate.
        assert section(report, "risk_analysis")["available"] is True
        assert section(report, "transaction_timeline")["available"] is True

    async def test_empty_evidence_is_available_with_note(self):
        report = await make_generator(evidence=[]).generate(
            CASE_ID, "detailed", generated_at=FIXED_TS
        )
        evidence_section = section(report, "evidence_references")
        assert evidence_section["available"] is True
        assert evidence_section["data"]["count"] == 0
        assert evidence_section["data"]["evidence"] == []
        assert evidence_section["note"]

    async def test_investigator_notes_reused_from_case_record(self):
        report = await make_generator().generate(CASE_ID, "detailed", generated_at=FIXED_TS)
        notes_section = section(report, "investigator_notes")
        assert notes_section["available"] is True
        assert notes_section["data"] == {
            "case_notes": "Victim reported loss after fake investment platform"
        }

        report_no_notes = await make_generator(
            case={**CASE, "investigator_notes": None}
        ).generate(CASE_ID, "detailed", generated_at=FIXED_TS)
        notes_missing = section(report_no_notes, "investigator_notes")
        assert notes_missing["available"] is False
        assert notes_missing["data"] is None
        assert notes_missing["reason"]


class TestReportIntegrity:
    async def test_no_fabricated_hashes_or_addresses(self):
        report = await make_generator().generate(CASE_ID, "detailed", generated_at=FIXED_TS)
        blob = json.dumps(report, default=str)

        allowed_hashes = {TX_HASH_1, TX_HASH_2}
        allowed_addresses = {WALLET, MID, DEST}
        for tx_hash in re.findall(r"(?<![a-f0-9])0x[a-f0-9]{64}(?![a-f0-9])", blob):
            assert tx_hash in allowed_hashes, tx_hash
        for address in re.findall(r"(?<![a-f0-9])0x[a-f0-9]{40}(?![a-f0-9])", blob):
            assert address in allowed_addresses, address

    async def test_deterministic_output(self):
        generator_a = make_generator()
        generator_b = make_generator()
        report_a = await generator_a.generate(CASE_ID, "detailed", generated_at=FIXED_TS)
        report_b = await generator_b.generate(CASE_ID, "detailed", generated_at=FIXED_TS)
        assert report_a == report_b

    async def test_step1_contract_sections_and_schema(self):
        report = await make_generator().generate(CASE_ID, "detailed", generated_at=FIXED_TS)
        assert [s["key"] for s in report["sections"]] == list(SECTION_ORDER)
        schema_keys = {"key", "title", "available", "data", "reason", "note"}
        for item in report["sections"]:
            assert set(item.keys()) == schema_keys

    async def test_evidence_export_type_includes_evidence_and_notes(self):
        report = await make_generator().generate(
            CASE_ID, "evidence_export", generated_at=FIXED_TS
        )
        keys = [s["key"] for s in report["sections"]]
        assert keys == list(REPORT_TYPE_SECTIONS["evidence_export"])
        assert "evidence_references" in keys
        assert "investigator_notes" in keys
        assert "vasp_attribution_results" not in keys

    async def test_invalid_type_format_and_missing_case_raise(self):
        generator = make_generator()
        with pytest.raises(InvalidReportTypeError):
            await generator.generate(CASE_ID, "memo", generated_at=FIXED_TS)
        with pytest.raises(InvalidReportTypeError):
            await generator.generate(CASE_ID, "detailed", "docx", generated_at=FIXED_TS)

        missing_case_generator = make_generator(case=None)
        with pytest.raises(ReportCaseNotFoundError):
            await missing_case_generator.generate(CASE_ID, "detailed", generated_at=FIXED_TS)
