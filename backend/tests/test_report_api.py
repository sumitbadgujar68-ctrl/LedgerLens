"""Phase 6 Step 4 — focused report API tests (docs/API_CONTRACT.md 4.9).

Covers the Step 4 contract only:
- POST create: 202 queued job response, job lifecycle, persisted content
- Validation: invalid report type/format -> 422; missing case -> 404
- GET list: documented shape, newest-first ordering, empty list, 404 case
- GET download: stored content verbatim, headers, deterministic bytes,
  404 missing/no-content report
- Generation failure: job marked failed, 500, nothing fabricated
- Regression: existing root/health behavior untouched
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from httpx import AsyncClient

from app.api.v1.reports import get_report_generator
from app.db.database import get_db
from app.db.models import Case, JobRecord, ReportRecord
from app.main import app
from app.models.report_schemas import ReportJobQueuedResponse
from app.services.reporting import (
    SECTION_ORDER,
    ReportGenerator,
    get_report_store,
    serialize_report,
)
from tests.test_report_aggregation import (
    ATTRIBUTION_ID,
    CASE_ID,
    EVIDENCE_ID_EARLY,
    PATTERN_ID,
    RISK_SCORE_ID,
    StubGrounding,
    TX_HASH_1,
    TX_HASH_2,
)

CASE_NUMBER = "LL-2026-0001"
OVERRODE_KEYS = (get_db, get_report_store, get_report_generator)


def make_case() -> Case:
    return Case(
        case_id=CASE_ID,
        case_number=CASE_NUMBER,
        title="Report API fixture case",
        reported_wallet_address="0x" + "1" * 40,
        blockchain="ethereum",
        fraud_type="investment_scam",
        investigator_id=UUID("00000000-0000-0000-0000-000000000001"),
        status="active",
        created_at=datetime(2026, 9, 21, tzinfo=timezone.utc),
    )


class FakeCaseDB:
    """Case-only session double: answers CaseService.get_case, no-ops writes."""

    def __init__(self, case: Optional[Case]) -> None:
        self.case = case

    async def execute(self, stmt, *args, **kwargs):
        compiled = stmt.compile()
        param_values = {str(v) for v in compiled.params.values()}
        matched = (
            self.case is not None and str(self.case.case_id) in param_values
        )

        class _Result:
            def scalar_one_or_none(self_inner):
                return self.case if matched else None

            def scalars(self_inner):
                return self_inner

            def all(self_inner):
                return []

        return _Result()

    def add(self, obj: Any) -> None:
        return None

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def refresh(self, obj: Any) -> None:
        return None


class StubStore:
    """In-memory ReportStore double recording lifecycle calls."""

    def __init__(self) -> None:
        self.jobs: List[JobRecord] = []
        self.reports: List[ReportRecord] = []
        self.calls: List[str] = []

    async def create_job(
        self, case_id, report_type, report_format, initiated_by, extra_parameters=None
    ) -> JobRecord:
        self.calls.append("create_job")
        job = JobRecord(
            job_id=uuid4(),
            job_type="report_generation",
            status="queued",
            progress=0,
            case_id=UUID(str(case_id)),
            initiated_by=UUID(str(initiated_by)),
            parameters={"report_type": report_type, "format": report_format},
            created_at=datetime.now(timezone.utc),
        )
        self.jobs.append(job)
        return job

    async def mark_job_started(self, job: JobRecord) -> JobRecord:
        self.calls.append("mark_job_started")
        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        return job

    async def mark_job_completed(
        self, job: JobRecord, result: Optional[Dict[str, Any]] = None
    ) -> JobRecord:
        self.calls.append("mark_job_completed")
        job.status = "completed"
        job.progress = 100
        job.result = result or {}
        job.completed_at = datetime.now(timezone.utc)
        return job

    async def mark_job_failed(self, job: JobRecord, error_message: str) -> JobRecord:
        self.calls.append("mark_job_failed")
        job.status = "failed"
        job.error_message = error_message
        job.completed_at = datetime.now(timezone.utc)
        return job

    async def save_report(self, report: Dict[str, Any], generated_by) -> ReportRecord:
        self.calls.append("save_report")
        record = ReportRecord(
            report_id=uuid4(),
            case_id=UUID(str(report.get("case_id"))),
            report_type=report["report_type"],
            format=report["format"],
            content=serialize_report(report),
            file_path=None,
            generated_by=UUID(str(generated_by)),
            generated_at=datetime.fromisoformat(str(report["generated_at"])),
        )
        self.reports.append(record)
        return record

    async def get_reports_for_case(self, case_id) -> List[ReportRecord]:
        self.calls.append("get_reports_for_case")
        matching = [r for r in self.reports if r.case_id == UUID(str(case_id))]
        return sorted(
            matching,
            key=lambda r: (r.generated_at is None, r.generated_at or datetime.min.replace(tzinfo=timezone.utc)),
            reverse=True,
        )

    async def get_report(self, report_id) -> Optional[ReportRecord]:
        self.calls.append("get_report")
        for record in self.reports:
            if record.report_id == UUID(str(report_id)):
                return record
        return None


class FailingGenerator:
    async def generate(self, *args, **kwargs):
        raise RuntimeError("generation exploded")


def fixture_generator() -> ReportGenerator:
    generator = ReportGenerator(None)
    generator.grounding = StubGrounding()
    return generator


def install_overrides(
    case: Optional[Case], store: Optional[Any] = None, generator: Optional[Any] = None
) -> None:
    async def _db_override():
        yield FakeCaseDB(case)

    app.dependency_overrides[get_db] = _db_override
    if store is not None:
        app.dependency_overrides[get_report_store] = lambda: store
    if generator is not None:
        app.dependency_overrides[get_report_generator] = lambda: generator


def cleanup_overrides() -> None:
    for key in OVERRODE_KEYS:
        app.dependency_overrides.pop(key, None)


async def test_post_report_creates_queued_job_and_persists_report():
    store = StubStore()
    install_overrides(make_case(), store, fixture_generator())
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/cases/{CASE_ID}/reports",
                json={"report_type": "detailed", "format": "json"},
            )
    finally:
        cleanup_overrides()

    assert response.status_code == 202
    body = response.json()
    assert set(body.keys()) == {"job_id", "status", "message"}
    assert body["status"] == "queued"
    assert body["message"] == "Report generation job queued"
    ReportJobQueuedResponse(**body)

    assert store.calls == [
        "create_job",
        "mark_job_started",
        "save_report",
        "mark_job_completed",
    ]
    assert len(store.jobs) == 1
    job = store.jobs[0]
    assert job.job_type == "report_generation"
    assert job.status == "completed"
    assert job.progress == 100

    assert len(store.reports) == 1
    record = store.reports[0]
    assert job.result == {"report_id": str(record.report_id)}
    assert record.case_id == CASE_ID

    data = json.loads(record.content)
    assert [s["key"] for s in data["sections"]] == list(SECTION_ORDER)
    graph = next(s for s in data["sections"] if s["key"] == "graph_summary")
    assert graph["available"] is False
    evidence = next(s for s in data["sections"] if s["key"] == "evidence_references")
    assert evidence["available"] is True
    assert evidence["data"]["count"] == 2


async def test_post_report_invalid_report_type_returns_422():
    store = StubStore()
    install_overrides(make_case(), store, fixture_generator())
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/cases/{CASE_ID}/reports",
                json={"report_type": "memo", "format": "json"},
            )
    finally:
        cleanup_overrides()

    assert response.status_code == 422
    assert store.jobs == []
    assert store.reports == []


async def test_post_report_invalid_format_returns_422():
    store = StubStore()
    install_overrides(make_case(), store, fixture_generator())
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/cases/{CASE_ID}/reports",
                json={"report_type": "detailed", "format": "docx"},
            )
    finally:
        cleanup_overrides()

    assert response.status_code == 422
    assert store.jobs == []


async def test_post_report_missing_case_returns_404():
    store = StubStore()
    install_overrides(None, store, fixture_generator())
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/cases/{CASE_ID}/reports",
                json={"report_type": "detailed", "format": "json"},
            )
    finally:
        cleanup_overrides()

    assert response.status_code == 404
    error = response.json()["detail"]["error"]
    assert error["code"] == "CASE_NOT_FOUND"
    assert store.jobs == []


async def test_get_reports_list_empty_returns_documented_shape():
    store = StubStore()
    install_overrides(make_case(), store, fixture_generator())
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/cases/{CASE_ID}/reports")
    finally:
        cleanup_overrides()

    assert response.status_code == 200
    assert response.json() == {"reports": []}


async def test_get_reports_list_orders_newest_first_with_documented_fields():
    store = StubStore()
    older = ReportRecord(
        report_id=uuid4(),
        case_id=CASE_ID,
        report_type="summary",
        format="json",
        generated_by=uuid4(),
        generated_at=datetime(2026, 9, 25, 10, 0, tzinfo=timezone.utc),
        content="{}",
    )
    newer = ReportRecord(
        report_id=uuid4(),
        case_id=CASE_ID,
        report_type="detailed",
        format="pdf",
        generated_by=uuid4(),
        generated_at=datetime(2026, 9, 25, 11, 0, tzinfo=timezone.utc),
        content="{}",
    )
    store.reports = [older, newer]
    install_overrides(make_case(), store, fixture_generator())
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/cases/{CASE_ID}/reports")
    finally:
        cleanup_overrides()

    assert response.status_code == 200
    items = response.json()["reports"]
    assert [i["report_id"] for i in items] == [
        str(newer.report_id),
        str(older.report_id),
    ]
    for item in items:
        assert set(item.keys()) == {
            "report_id",
            "report_type",
            "format",
            "generated_at",
            "file_url",
        }
        assert item["file_url"] == f"/api/v1/reports/{item['report_id']}/download"


async def test_get_reports_list_missing_case_returns_404():
    install_overrides(None, StubStore(), fixture_generator())
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/cases/{CASE_ID}/reports")
    finally:
        cleanup_overrides()

    assert response.status_code == 404
    assert response.json()["detail"]["error"]["code"] == "CASE_NOT_FOUND"


async def test_download_returns_stored_content_deterministically():
    store = StubStore()
    install_overrides(make_case(), store, fixture_generator())
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            post = await client.post(
                f"/api/v1/cases/{CASE_ID}/reports",
                json={"report_type": "detailed", "format": "json"},
            )
            assert post.status_code == 202
            report_id = store.reports[0].report_id

            first = await client.get(f"/api/v1/reports/{report_id}/download")
            second = await client.get(f"/api/v1/reports/{report_id}/download")
    finally:
        cleanup_overrides()

    assert first.status_code == 200
    assert first.headers["content-type"].startswith("application/json")
    disposition = first.headers["content-disposition"]
    assert disposition == f'attachment; filename="{CASE_NUMBER}_report.json"'

    # Persisted bytes are returned verbatim and are byte-stable across GETs.
    stored = store.reports[0].content
    assert first.content.decode("utf-8") == stored
    assert second.content == first.content

    # Deterministic serialization: re-serializing the parsed payload is a
    # byte-identical round trip.
    parsed = json.loads(first.content)
    assert serialize_report(parsed) == stored

    # Provenance survives the API boundary.
    for provenance_id in (
        TX_HASH_1,
        TX_HASH_2,
        str(PATTERN_ID),
        str(ATTRIBUTION_ID),
        str(RISK_SCORE_ID),
        str(EVIDENCE_ID_EARLY),
    ):
        assert provenance_id in stored
    assert [s["key"] for s in parsed["sections"]] == list(SECTION_ORDER)


async def test_download_missing_report_returns_404():
    install_overrides(make_case(), StubStore(), fixture_generator())
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/reports/{uuid4()}/download")
    finally:
        cleanup_overrides()

    assert response.status_code == 404
    assert response.json()["detail"]["error"]["code"] == "REPORT_NOT_FOUND"


async def test_download_report_without_content_returns_404():
    store = StubStore()
    record = ReportRecord(
        report_id=uuid4(),
        case_id=CASE_ID,
        report_type="detailed",
        format="json",
        generated_by=uuid4(),
        generated_at=datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc),
        content=None,
    )
    store.reports = [record]
    install_overrides(make_case(), store, fixture_generator())
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/reports/{record.report_id}/download")
    finally:
        cleanup_overrides()

    assert response.status_code == 404
    assert response.json()["detail"]["error"]["code"] == "REPORT_NOT_AVAILABLE"


async def test_generation_failure_marks_job_failed_and_returns_500():
    store = StubStore()
    install_overrides(make_case(), store, FailingGenerator())
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/cases/{CASE_ID}/reports",
                json={"report_type": "detailed", "format": "json"},
            )
    finally:
        cleanup_overrides()

    assert response.status_code == 500
    assert response.json()["detail"]["error"]["code"] == "REPORT_GENERATION_ERROR"
    assert len(store.jobs) == 1
    assert store.jobs[0].status == "failed"
    assert "generation exploded" in store.jobs[0].error_message
    assert store.reports == []  # nothing fabricated on failure


async def test_existing_api_behavior_unchanged():
    async with AsyncClient(app=app, base_url="http://test") as client:
        health = await client.get("/health")
        root = await client.get("/")
        missing_route = await client.get("/api/v1/reports/not-a-uuid/download")

    assert health.status_code == 200
    assert health.json() == {"status": "healthy"}
    root_body = root.json()
    assert root_body["service"] == "LedgerLens API"
    assert "Phase 5" in root_body["phase"]  # Phase 1-5 surface untouched
    assert missing_route.status_code == 422  # path validation still enforced
