"""Phase 6 Step 3 — focused report schemas/models/persistence tests.

Covers the Step 3 contract only:
- reports/jobs model conformance to docs/DATA_MODEL.md 4.13-4.14
- Report request/response schemas matching docs/API_CONTRACT.md 4.9
- ReportDataResponse fidelity to the Step 1/2 generator contract
- Deterministic serialization with provenance and unavailable-data round-trip
- ReportStore job lifecycle and report storage primitives
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects.postgresql import JSONB

from app.db.models import JobRecord, ReportRecord
from app.models.report_schemas import (
    ReportDataResponse,
    ReportGenerateRequest,
    ReportJobQueuedResponse,
    ReportListItemResponse,
    ReportListResponse,
    ReportMetadataResponse,
)
from app.services.reporting import (
    REPORT_GENERATION_JOB_TYPE,
    InvalidReportTypeError,
    ReportStore,
    deserialize_report,
    get_report_store,
    serialize_report,
)
from tests.test_report_aggregation import (
    ATTRIBUTION_ID,
    CASE_ID,
    EVIDENCE_ID_EARLY,
    EVIDENCE_ID_LATE,
    FIXED_TS,
    INVESTIGATOR_ID,
    PATTERN_ID,
    RISK_SCORE_ID,
    TRACE_ID,
    TX_HASH_1,
    TX_HASH_2,
    make_generator,
)

REPORT_ID = uuid4()
JOB_ID = uuid4()


class FakeSession:
    """Minimal AsyncSession double covering add/flush/execute paths."""

    def __init__(self, rows: Optional[List[Any]] = None, single: Any = None) -> None:
        self.added: List[Any] = []
        self.flush_count = 0
        self.statements: List[Any] = []
        self.rows = rows or []
        self.single = single

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        self.flush_count += 1

    async def execute(self, stmt: Any):
        self.statements.append(stmt)
        rows = self.rows
        single = self.single

        class _Result:
            def scalars(self_inner):
                return self_inner

            def all(self_inner):
                return list(rows)

            def scalar_one_or_none(self_inner):
                return single

        return _Result()


async def _make_report(**stub_kwargs: Any) -> Dict[str, Any]:
    return await make_generator(**stub_kwargs).generate(
        CASE_ID, "detailed", generated_at=FIXED_TS
    )


class TestPersistenceModels:
    def test_reports_model_matches_data_model_4_13(self):
        assert ReportRecord.__tablename__ == "reports"
        columns = ReportRecord.__table__.columns
        assert set(columns.keys()) == {
            "report_id",
            "case_id",
            "report_type",
            "format",
            "content",
            "file_path",
            "generated_by",
            "generated_at",
        }
        assert columns["report_id"].primary_key is True
        assert columns["report_id"].default is not None
        assert columns["case_id"].nullable is False
        assert columns["report_type"].nullable is False
        assert columns["format"].nullable is False
        assert columns["content"].nullable is True
        assert columns["file_path"].nullable is True
        assert columns["generated_by"].nullable is False
        assert columns["generated_at"].server_default is not None
        assert columns["case_id"].index is True
        assert columns["generated_by"].index is True
        assert columns["generated_at"].index is True

    def test_jobs_model_matches_data_model_4_14(self):
        assert JobRecord.__tablename__ == "jobs"
        columns = JobRecord.__table__.columns
        assert set(columns.keys()) == {
            "job_id",
            "job_type",
            "status",
            "progress",
            "case_id",
            "initiated_by",
            "parameters",
            "result",
            "error_message",
            "started_at",
            "completed_at",
            "created_at",
        }
        assert columns["job_id"].primary_key is True
        assert columns["job_id"].default is not None
        assert columns["job_type"].nullable is False
        assert columns["status"].nullable is False
        assert columns["status"].default.arg == "queued"
        assert columns["progress"].default.arg == 0
        assert columns["case_id"].nullable is True
        assert columns["initiated_by"].nullable is False
        assert columns["parameters"].nullable is True
        assert columns["result"].nullable is True
        assert isinstance(columns["parameters"].type, JSONB)
        assert isinstance(columns["result"].type, JSONB)
        assert columns["error_message"].nullable is True
        assert columns["started_at"].nullable is True
        assert columns["completed_at"].nullable is True
        assert columns["created_at"].server_default is not None
        assert columns["status"].index is True
        assert columns["case_id"].index is True
        assert columns["created_at"].index is True


class TestReportSchemas:
    def test_generate_request_accepts_documented_enums(self):
        for report_type in ("summary", "detailed", "evidence_export"):
            request = ReportGenerateRequest(report_type=report_type, format="json")
            assert request.report_type == report_type
            assert request.format == "json"
        for report_format in ("pdf", "json", "html"):
            request = ReportGenerateRequest(report_type="detailed", format=report_format)
            assert request.format == report_format

    def test_generate_request_rejects_undocumented_values(self):
        with pytest.raises(ValidationError):
            ReportGenerateRequest(report_type="memo", format="json")
        with pytest.raises(ValidationError):
            ReportGenerateRequest(report_type="detailed", format="docx")

    def test_job_queued_response_matches_documented_contract(self):
        response = ReportJobQueuedResponse(job_id=JOB_ID)
        dumped = response.model_dump()
        assert set(dumped.keys()) == {"job_id", "status", "message"}
        assert dumped["job_id"] == JOB_ID
        assert dumped["status"] == "queued"
        assert dumped["message"] == "Report generation job queued"

    def test_report_list_item_and_metadata_shapes(self):
        item = ReportListItemResponse(
            report_id=REPORT_ID,
            report_type="detailed",
            format="pdf",
            generated_at=datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc),
            file_url=f"/api/v1/reports/{REPORT_ID}/download",
        )
        dumped = item.model_dump()
        assert set(dumped.keys()) == {
            "report_id",
            "report_type",
            "format",
            "generated_at",
            "file_url",
        }
        assert dumped["file_url"].endswith("/download")

        listing = ReportListResponse(reports=[item])
        assert listing.reports[0].report_id == REPORT_ID

        metadata = ReportMetadataResponse(**dumped)
        assert metadata.report_id == REPORT_ID

    async def test_report_data_response_round_trips_generator_output(self):
        report = await _make_report()
        validated = ReportDataResponse.model_validate(report)
        assert validated.model_dump() == report


class TestDeterministicSerialization:
    async def test_serialize_is_order_independent_and_stable(self):
        report = await _make_report()
        shuffled = dict(reversed(list(report.items())))
        first = serialize_report(report)
        second = serialize_report(report)
        assert first == second
        assert first == serialize_report(shuffled)

    async def test_round_trip_preserves_provenance_and_availability(self):
        report = await _make_report()
        restored = deserialize_report(serialize_report(report))
        assert restored == report

        blob = serialize_report(restored)
        for provenance_id in (
            TX_HASH_1,
            TX_HASH_2,
            str(PATTERN_ID),
            str(ATTRIBUTION_ID),
            str(RISK_SCORE_ID),
            str(TRACE_ID),
            str(EVIDENCE_ID_EARLY),
            str(EVIDENCE_ID_LATE),
        ):
            assert provenance_id in blob

        sections = {s["key"]: s for s in restored["sections"]}
        assert sections["graph_summary"]["available"] is False
        assert sections["graph_summary"]["reason"]
        assert sections["evidence_references"]["available"] is True
        assert sections["evidence_references"]["data"]["count"] == 2
        assert "graph_summary" in restored["unavailable_sections"]

    def test_deserialize_rejects_non_object_payloads(self):
        with pytest.raises(ValueError):
            deserialize_report("[1, 2, 3]")
        with pytest.raises(ValueError):
            deserialize_report('"just a string"')
        with pytest.raises(ValueError):
            deserialize_report("{not json")


class TestReportStore:
    async def test_create_job_defaults_and_parameters(self):
        session = FakeSession()
        store = get_report_store(session)
        assert isinstance(store, ReportStore)

        job = await store.create_job(CASE_ID, "detailed", "json", INVESTIGATOR_ID)

        assert session.added == [job]
        assert job.job_type == REPORT_GENERATION_JOB_TYPE == "report_generation"
        assert job.status == "queued"
        assert job.progress == 0
        assert job.case_id == CASE_ID
        assert job.initiated_by == INVESTIGATOR_ID
        assert job.parameters == {"report_type": "detailed", "format": "json"}

        job_with_extras = await store.create_job(
            CASE_ID, "summary", "pdf", INVESTIGATOR_ID,
            extra_parameters={"locale": "en"},
        )
        assert job_with_extras.parameters == {
            "report_type": "summary",
            "format": "pdf",
            "locale": "en",
        }

    async def test_create_job_validates_documented_enums_and_required_fields(self):
        store = ReportStore(FakeSession())
        with pytest.raises(InvalidReportTypeError):
            await store.create_job(CASE_ID, "memo", "json", INVESTIGATOR_ID)
        with pytest.raises(InvalidReportTypeError):
            await store.create_job(CASE_ID, "detailed", "docx", INVESTIGATOR_ID)
        with pytest.raises(ValueError):
            await store.create_job(CASE_ID, "detailed", "json", None)

    async def test_save_report_round_trips_content(self):
        report = await _make_report()
        session = FakeSession()
        store = ReportStore(session)

        record = await store.save_report(report, INVESTIGATOR_ID)

        assert session.added == [record]
        assert record.case_id == CASE_ID
        assert record.report_type == "detailed"
        assert record.format == "json"
        assert record.generated_by == INVESTIGATOR_ID
        assert record.generated_at == FIXED_TS
        assert record.file_path is None
        assert deserialize_report(record.content) == report

    async def test_save_report_validates_type_format_and_generated_by(self):
        report = await _make_report()
        store = ReportStore(FakeSession())

        with pytest.raises(InvalidReportTypeError):
            await store.save_report({**report, "report_type": "memo"}, INVESTIGATOR_ID)
        with pytest.raises(InvalidReportTypeError):
            await store.save_report({**report, "format": "docx"}, INVESTIGATOR_ID)
        with pytest.raises(ValueError):
            await store.save_report(report, None)

    async def test_job_lifecycle_states(self):
        session = FakeSession()
        store = ReportStore(session)

        job = await store.create_job(CASE_ID, "detailed", "json", INVESTIGATOR_ID)
        await store.mark_job_started(job)
        assert job.status == "processing"
        assert job.started_at is not None
        assert job.completed_at is None

        await store.mark_job_completed(job, result={"report_id": str(REPORT_ID)})
        assert job.status == "completed"
        assert job.progress == 100
        assert job.result == {"report_id": str(REPORT_ID)}
        assert job.completed_at is not None

        failed_job = await store.create_job(CASE_ID, "summary", "pdf", INVESTIGATOR_ID)
        await store.mark_job_failed(failed_job, "generation exploded")
        assert failed_job.status == "failed"
        assert failed_job.error_message == "generation exploded"
        assert failed_job.completed_at is not None
        assert failed_job.progress == 0

    async def test_get_reports_for_case_orders_newest_first(self):
        row = ReportRecord(
            report_id=REPORT_ID,
            case_id=CASE_ID,
            report_type="detailed",
            format="json",
            generated_by=INVESTIGATOR_ID,
        )
        session = FakeSession(rows=[row])
        store = ReportStore(session)

        reports = await store.get_reports_for_case(CASE_ID)

        assert reports == [row]
        sql = str(session.statements[0].compile())
        assert "WHERE reports.case_id =" in sql
        assert "ORDER BY reports.generated_at DESC" in sql

    async def test_get_report_and_get_job_lookup_by_id(self):
        report_row = ReportRecord(
            report_id=REPORT_ID,
            case_id=CASE_ID,
            report_type="detailed",
            format="json",
            generated_by=INVESTIGATOR_ID,
        )
        store = ReportStore(FakeSession(single=report_row))
        assert await store.get_report(REPORT_ID) == report_row

        missing_store = ReportStore(FakeSession(single=None))
        assert await missing_store.get_report(REPORT_ID) is None
        assert await missing_store.get_job(JOB_ID) is None

    def test_get_report_data_deserializes_and_requires_content(self):
        stored = ReportRecord(
            report_id=REPORT_ID,
            case_id=CASE_ID,
            report_type="detailed",
            format="json",
            generated_by=INVESTIGATOR_ID,
            content='{"case_id": "x", "sections": []}',
        )
        store = ReportStore(FakeSession())
        assert store.get_report_data(stored) == {"case_id": "x", "sections": []}

        empty = ReportRecord(
            report_id=REPORT_ID,
            case_id=CASE_ID,
            report_type="detailed",
            format="json",
            generated_by=INVESTIGATOR_ID,
            content=None,
        )
        with pytest.raises(ValueError):
            store.get_report_data(empty)
