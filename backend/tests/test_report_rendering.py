"""Phase 6 Step 5 — focused report export rendering tests.

Covers the Step 5 contract only:
- HTML generation with the documented report section ordering (ROADMAP.md)
- HTML sanitization: report data can never become executable markup
- JSON generation with deterministic serialization and provenance fidelity
- PDF generation, determinism, and the explicit renderer-unavailable path
- Correct download media types
- ReportRecord artifact fields (file_path) and persisted content contract
- Unavailable evidence/data propagation into every export format
- Regression of Step 1-4 report generation, persistence, and API behavior
"""

import importlib.util
import re
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.db.models import JobRecord, ReportRecord
from app.main import app
from app.services.reporting import (
    MEDIA_TYPES,
    ARTIFACT_FORMATS,
    InvalidReportTypeError,
    PdfRendererUnavailableError,
    ReportArtifactNotFoundError,
    ReportArtifactStore,
    ReportStore,
    SECTION_ORDER,
    SECTION_TITLES,
    deserialize_report,
    render_html,
    render_json,
    render_pdf,
    render_report,
    serialize_report,
)
from app.services.reporting import render as render_module
from tests.test_report_aggregation import (
    ATTRIBUTION_ID,
    CASE,
    CASE_ID,
    EVIDENCE_ID_EARLY,
    EVIDENCE_ID_LATE,
    FIXED_TS,
    PATTERN_ID,
    RISK_SCORE_ID,
    TRACE_ID,
    TX_HASH_1,
    TX_HASH_2,
    make_generator,
)
from tests.test_report_api import (
    cleanup_overrides,
    fixture_generator,
    install_overrides,
    make_case,
)

PDF_AVAILABLE = importlib.util.find_spec("reportlab") is not None
requires_pdf_renderer = pytest.mark.skipif(
    not PDF_AVAILABLE, reason="reportlab PDF renderer not installed"
)

# The 14 documented report sections (docs/ROADMAP.md Phase 6 deliverables).
ROADMAP_SECTIONS: List[str] = [
    "case_information",
    "initial_reported_wallet",
    "investigation_methodology",
    "transaction_timeline",
    "graph_summary",
    "intermediary_wallets",
    "destination_entities",
    "vasp_attribution_results",
    "risk_analysis",
    "detected_patterns",
    "evidence_references",
    "investigator_notes",
    "limitations_and_disclaimers",
    "generated_timestamp",
]

XSS_PAYLOAD = '<script>alert("xss")</script><img src=x onerror=alert(1)>'


async def make_report(
    report_format: str = "html", report_type: str = "detailed", **stub_kwargs: Any
) -> Dict[str, Any]:
    return await make_generator(**stub_kwargs).generate(
        CASE_ID, report_type, report_format, generated_at=FIXED_TS
    )


def report_section(report: Dict[str, Any], key: str) -> Dict[str, Any]:
    return next(s for s in report["sections"] if s["key"] == key)


class ArtifactSession:
    """AsyncSession double that records Report/Job rows for the API tests."""

    def __init__(self) -> None:
        self.reports: List[ReportRecord] = []
        self.jobs: List[JobRecord] = []

    def add(self, obj: Any) -> None:
        if isinstance(obj, ReportRecord):
            self.reports.append(obj)
        elif isinstance(obj, JobRecord):
            self.jobs.append(obj)

    async def flush(self) -> None:
        # Mirror the database: server-side primary key defaults are assigned
        # at flush time (jobs.job_id is a Python-side uuid4 default).
        for obj in self.jobs:
            if obj.job_id is None:
                obj.job_id = uuid4()
        for obj in self.reports:
            if obj.report_id is None:
                obj.report_id = uuid4()
        return None

    async def commit(self) -> None:
        return None

    async def refresh(self, obj: Any) -> None:
        return None

    async def execute(self, stmt: Any):
        values = {str(v) for v in stmt.compile().params.values()}
        rows = [r for r in self.reports if str(r.report_id) in values]
        if not rows:
            rows = [r for r in self.reports if str(r.case_id) in values]

        class _Result:
            def scalars(self_inner):
                return _Result()

            def all(self_inner):
                return list(rows)

            def scalar_one_or_none(self_inner):
                return rows[0] if rows else None

        return _Result()


def make_store(root_dir: Path) -> ReportStore:
    return ReportStore(ArtifactSession(), artifacts=ReportArtifactStore(root_dir))


# ----------------------------------------------------------------------
# Documented section order
# ----------------------------------------------------------------------


class TestDocumentedSectionOrder:
    def test_section_order_matches_roadmap_deliverables(self):
        assert list(SECTION_ORDER) == ROADMAP_SECTIONS
        assert len(SECTION_ORDER) == 14

    def test_every_documented_section_has_a_title(self):
        assert set(SECTION_TITLES) == set(SECTION_ORDER)
        assert all(SECTION_TITLES[key] for key in SECTION_ORDER)


# ----------------------------------------------------------------------
# HTML
# ----------------------------------------------------------------------


class TestHtmlRendering:
    async def test_html_renders_sections_in_documented_order(self):
        report = await make_report("html")
        html = render_html(report)

        assert html.startswith("<!DOCTYPE html>")
        headings = re.findall(r"<h2>(\d+)\. (.*?)</h2>", html)
        assert [int(position) for position, _ in headings] == list(range(1, 15))
        assert [title for _, title in headings] == [
            SECTION_TITLES[key] for key in ROADMAP_SECTIONS
        ]

    async def test_html_includes_report_metadata_header(self):
        report = await make_report("html")
        html = render_html(report)

        assert "<h1>LedgerLens Investigation Report</h1>" in html
        assert "LL-2026-0001" in html
        assert str(CASE_ID) in html
        assert "Report type" in html
        assert "detailed" in html
        assert FIXED_TS.isoformat() in html
        assert "graph_summary" in html  # unavailable_sections surfaced

    async def test_html_marks_unavailable_sections_with_reason(self):
        report = await make_report(
            "html", evidence_error=RuntimeError("relation does not exist")
        )
        html = render_html(report)

        # Unavailable section keeps available=false + reason, no fabricated data.
        assert 'class="section unavailable"' in html
        assert "Unavailable: Evidence store unavailable" in html
        assert report_section(report, "evidence_references")["available"] is False
        assert report_section(report, "evidence_references")["data"] is None
        assert "evidence_id" not in html.split(
            'id="evidence_references"'
        )[1].split("</section>")[0]
        # Graph summary stays unavailable in the fixture (no trace graph).
        assert "No transaction graph generated for this case" in html
        # Unavailability is scoped: other sections still render their data.
        assert 'class="section available"' in html
        assert TX_HASH_1 in html

    async def test_html_escapes_user_controlled_text(self):
        report = await make_report(
            "html",
            case={**CASE, "title": XSS_PAYLOAD, "investigator_notes": XSS_PAYLOAD},
        )
        html = render_html(report)

        assert "<script" not in html
        assert "<img" not in html
        assert "&lt;script&gt;" in html
        assert "onerror=alert(1)" in html  # present only as escaped text
        assert 'onerror="' not in html

    async def test_html_contains_no_executable_markup(self):
        report = await make_report(
            "html", case={**CASE, "title": XSS_PAYLOAD}
        )
        html = render_html(report)

        assert "<script" not in html.lower()
        assert "javascript:" not in html.lower()
        # No event handler may ever appear inside markup (only as escaped text).
        assert re.search(r"<[^>]*\son(?:error|load|click|mouseover)\s*=", html) is None
        assert "<iframe" not in html.lower()
        assert "<object" not in html.lower()
        # Defense in depth: a strict CSP plus no-referrer metadata.
        assert "Content-Security-Policy" in html
        assert "script-src 'none'" in html
        assert '<meta name="referrer" content="no-referrer">' in html

    async def test_html_output_is_deterministic(self):
        first = await make_report("html")
        second = await make_report("html")
        assert render_html(first) == render_html(second)

        # Envelope key order never changes the rendered document.
        shuffled = dict(reversed(list(first.items())))
        assert render_html(shuffled) == render_html(first)

    async def test_html_preserves_notes_empty_findings_and_disclaimers(self):
        report = await make_report("html", evidence=[])
        html = render_html(report)

        assert "No investigator evidence pinned for this case" in html
        assert "This report is investigative intelligence" in html
        assert "All findings require human investigator verification" in html
        assert FIXED_TS.isoformat() in html

    async def test_html_never_fabricates_unavailable_evidence(self):
        report = await make_report(
            "html", evidence_error=RuntimeError("relation does not exist")
        )
        html = render_html(report)
        evidence_block = html.split('id="evidence_references"')[1].split("</section>")[0]

        assert "Evidence store unavailable" in evidence_block
        assert str(EVIDENCE_ID_EARLY) not in evidence_block
        assert str(EVIDENCE_ID_LATE) not in evidence_block
        assert "evidence_references" in report["unavailable_sections"]


# ----------------------------------------------------------------------
# JSON
# ----------------------------------------------------------------------


class TestJsonRendering:
    async def test_json_matches_store_serialization_contract(self):
        report = await make_report("json")
        assert render_json(report) == serialize_report(report)
        assert deserialize_report(render_json(report)) == report

    async def test_json_preserves_provenance_and_unavailable_data(self):
        report = await make_report(
            "json", evidence_error=RuntimeError("relation does not exist")
        )
        payload = render_json(report)

        for provenance_id in (
            TX_HASH_1,
            TX_HASH_2,
            str(PATTERN_ID),
            str(ATTRIBUTION_ID),
            str(RISK_SCORE_ID),
            str(TRACE_ID),
        ):
            assert provenance_id in payload

        parsed = deserialize_report(payload)
        assert [s["key"] for s in parsed["sections"]] == ROADMAP_SECTIONS
        assert "graph_summary" in parsed["unavailable_sections"]
        assert "evidence_references" in parsed["unavailable_sections"]
        evidence = report_section(parsed, "evidence_references")
        assert evidence["available"] is False
        assert evidence["data"] is None
        assert "Evidence store unavailable" in evidence["reason"]

    async def test_json_is_deterministic_and_key_order_independent(self):
        first = await make_report("json")
        second = await make_report("json")

        assert render_json(first) == render_json(second)
        assert render_json(dict(reversed(list(first.items())))) == render_json(first)
        # Sorted keys: the payload is stable regardless of insertion order.
        assert render_json(first) == render_json(
            deserialize_report(render_json(first))
        )

    async def test_json_preserves_empty_findings_notes(self):
        report = await make_report("json", evidence=[])
        evidence = report_section(report, "evidence_references")
        assert evidence["available"] is True
        assert evidence["data"] == {"count": 0, "evidence": []}
        assert evidence["note"] == "No investigator evidence pinned for this case"
        assert "evidence_references" not in report["unavailable_sections"]


# ----------------------------------------------------------------------
# PDF
# ----------------------------------------------------------------------


class TestPdfRendering:
    @requires_pdf_renderer
    async def test_pdf_generation_produces_pdf_document(self):
        report = await make_report("pdf")
        pdf = render_pdf(report)

        assert isinstance(pdf, bytes)
        assert pdf.startswith(b"%PDF-")
        assert pdf.rstrip().endswith(b"%%EOF")
        assert b"LedgerLens Investigation Report" in pdf

    @requires_pdf_renderer
    async def test_pdf_output_is_deterministic(self):
        first = await make_report("pdf")
        second = await make_report("pdf")

        assert render_pdf(first) == render_pdf(second)
        assert render_report(first, "pdf") == render_pdf(first)

    @requires_pdf_renderer
    async def test_pdf_preserves_section_order_and_metadata(self):
        report = await make_report("pdf")
        pdf = render_pdf(report)

        positions = [
            pdf.index(SECTION_TITLES[key].encode("latin-1", "replace"))
            for key in ROADMAP_SECTIONS
        ]
        assert positions == sorted(positions)
        assert pdf.index(b"LedgerLens Investigation Report") < positions[0]
        assert FIXED_TS.isoformat().encode() in pdf
        assert b"This report is investigative intelligence" in pdf

    @requires_pdf_renderer
    async def test_pdf_preserves_unavailable_data_semantics(self):
        report = await make_report(
            "pdf", evidence_error=RuntimeError("relation does not exist")
        )
        pdf = render_pdf(report)

        assert b"Status: unavailable" in pdf
        assert b"Evidence store unavailable" in pdf
        assert b"Status: available" in pdf
        assert TX_HASH_1.encode() in pdf

    async def test_pdf_renderer_unavailable_raises_explicit_error(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        def _raise():
            raise ImportError("reportlab unavailable")

        monkeypatch.setattr(render_module, "_import_reportlab", _raise)

        report = await make_report("pdf")
        with pytest.raises(PdfRendererUnavailableError) as excinfo:
            render_pdf(report)

        message = str(excinfo.value)
        assert "PDF rendering is unavailable" in message
        assert "reportlab" in message
        # The limitation is explicit; no fake PDF bytes are produced.
        assert not message.startswith("%PDF")

    async def test_pdf_renderer_unavailable_reported_by_dispatch(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        def _raise():
            raise ImportError("reportlab unavailable")

        monkeypatch.setattr(render_module, "_import_reportlab", _raise)
        report = await make_report("pdf")

        with pytest.raises(PdfRendererUnavailableError):
            render_report(report, "pdf")
        # HTML/JSON export are unaffected by the missing PDF renderer.
        assert render_report(report, "html").startswith(b"<!DOCTYPE html>")
        assert render_report(report, "json").startswith(b"{")


# ----------------------------------------------------------------------
# Dispatch / content types
# ----------------------------------------------------------------------


class TestRenderDispatch:
    def test_media_types_match_documented_formats(self):
        assert MEDIA_TYPES == {
            "json": "application/json",
            "html": "text/html",
            "pdf": "application/pdf",
        }

    async def test_render_report_dispatches_html_and_json(self):
        report = await make_report("html")
        assert render_report(report, "html") == render_html(report).encode("utf-8")
        assert render_report(report, "json") == render_json(report).encode("utf-8")

    async def test_unknown_format_is_rejected(self):
        report = await make_report("json")
        with pytest.raises(InvalidReportTypeError):
            render_report(report, "docx")

    def test_only_file_formats_declared_as_artifacts(self):
        assert set(ARTIFACT_FORMATS) == {"html", "pdf"}


# ----------------------------------------------------------------------
# ReportRecord artifact integration
# ----------------------------------------------------------------------


class TestReportRecordArtifacts:
    async def test_save_html_report_writes_artifact_and_sets_file_path(
        self, tmp_path: Path
    ):
        report = await make_report("html")
        store = make_store(tmp_path)

        record = await store.save_report(report, uuid4())

        assert record.file_path is not None
        artifact = Path(record.file_path)
        assert artifact.suffix == ".html"
        assert artifact.parent == tmp_path
        assert str(CASE_ID) in str(record.case_id)
        assert artifact.is_file()
        assert artifact.read_bytes() == render_html(report).encode("utf-8")
        assert record.format == "html"
        # Persisted content stays deterministic JSON (ReportStore contract).
        assert record.content == serialize_report(report)
        assert deserialize_report(record.content) == report

    async def test_save_json_report_keeps_file_path_none(self, tmp_path: Path):
        report = await make_report("json")
        store = make_store(tmp_path)

        record = await store.save_report(report, uuid4())

        assert record.file_path is None
        assert list(tmp_path.iterdir()) == []
        assert deserialize_report(record.content) == report

    @requires_pdf_renderer
    async def test_save_pdf_report_writes_artifact(self, tmp_path: Path):
        report = await make_report("pdf")
        store = make_store(tmp_path)

        record = await store.save_report(report, uuid4())

        assert record.file_path is not None
        artifact = Path(record.file_path)
        assert artifact.suffix == ".pdf"
        assert artifact.read_bytes().startswith(b"%PDF-")
        assert deserialize_report(record.content) == report

    async def test_read_artifact_returns_persisted_bytes(
        self, tmp_path: Path
    ):
        report = await make_report("html")
        store = make_store(tmp_path)
        record = await store.save_report(report, uuid4())

        assert store.read_artifact(record) == render_html(report).encode("utf-8")

    async def test_read_artifact_rejects_missing_file(self, tmp_path: Path):
        report = await make_report("html")
        store = make_store(tmp_path)
        record = await store.save_report(report, uuid4())

        Path(record.file_path).unlink()
        with pytest.raises(ReportArtifactNotFoundError):
            store.read_artifact(record)

        unsaved = ReportRecord(
            report_id=uuid4(),
            case_id=CASE_ID,
            report_type="detailed",
            format="html",
            generated_by=uuid4(),
        )
        with pytest.raises(ReportArtifactNotFoundError):
            store.read_artifact(unsaved)

    async def test_artifact_store_rejects_paths_outside_root(
        self, tmp_path: Path
    ):
        store = ReportArtifactStore(tmp_path)
        outside = Path(__file__).resolve()

        with pytest.raises(ReportArtifactNotFoundError):
            store.read(outside)

    async def test_artifact_store_rejects_inline_json_format(
        self, tmp_path: Path
    ):
        store = ReportArtifactStore(tmp_path)
        report = await make_report("json")

        with pytest.raises(InvalidReportTypeError):
            store.path_for(report, uuid4())


# ----------------------------------------------------------------------
# Report API export behavior (Step 4 regression + Step 5 download)
# ----------------------------------------------------------------------


async def _post_and_download(store: ReportStore, report_format: str):
    session = store.db
    install_overrides(make_case(), store, fixture_generator())
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            post = await client.post(
                f"/api/v1/cases/{CASE_ID}/reports",
                json={"report_type": "detailed", "format": report_format},
            )
            assert post.status_code == 202, post.text
            record = session.reports[0]
            download = await client.get(
                f"/api/v1/reports/{record.report_id}/download"
            )
            second = await client.get(
                f"/api/v1/reports/{record.report_id}/download"
            )
    finally:
        cleanup_overrides()
    return record, download, second


class TestReportApiExport:
    async def test_html_report_download_serves_rendered_artifact(
        self, tmp_path: Path
    ):
        store = make_store(tmp_path)
        record, download, second = await _post_and_download(store, "html")

        assert record.file_path is not None
        assert record.file_path.endswith(".html")
        assert download.status_code == 200
        assert download.headers["content-type"].startswith("text/html")
        assert (
            download.headers["content-disposition"]
            == f'attachment; filename="LL-2026-0001_report.html"'
        )
        body = download.content.decode("utf-8")
        assert body.startswith("<!DOCTYPE html>")
        assert "<script" not in body
        # Persisted content contract is untouched: content is still JSON.
        assert deserialize_report(record.content)["sections"]
        # Download serves the artifact verbatim (no regeneration).
        assert download.content == Path(record.file_path).read_bytes()
        assert second.content == download.content

    async def test_html_download_does_not_rerender_artifact(
        self, tmp_path: Path
    ):
        store = make_store(tmp_path)
        record, download, second = await _post_and_download(store, "html")
        artifact = Path(record.file_path)
        before = artifact.read_bytes()
        stat_before = artifact.stat().st_mtime_ns

        assert download.content == before
        assert second.content == before
        assert artifact.read_bytes() == before
        assert artifact.stat().st_mtime_ns == stat_before

    @requires_pdf_renderer
    async def test_pdf_report_download_serves_pdf_artifact(
        self, tmp_path: Path
    ):
        store = make_store(tmp_path)
        record, download, second = await _post_and_download(store, "pdf")

        assert record.file_path is not None
        assert record.file_path.endswith(".pdf")
        assert download.status_code == 200
        assert download.headers["content-type"] == "application/pdf"
        assert (
            download.headers["content-disposition"]
            == f'attachment; filename="LL-2026-0001_report.pdf"'
        )
        assert download.content.startswith(b"%PDF-")
        assert second.content == download.content

    async def test_json_report_api_behavior_unchanged(
        self, tmp_path: Path
    ):
        """Step 3/4 regression: JSON reports stay inline and download verbatim."""
        store = make_store(tmp_path)
        record, download, second = await _post_and_download(store, "json")

        assert record.file_path is None
        assert list(tmp_path.iterdir()) == []
        assert download.status_code == 200
        assert download.headers["content-type"].startswith("application/json")
        assert (
            download.headers["content-disposition"]
            == f'attachment; filename="LL-2026-0001_report.json"'
        )
        assert download.content.decode("utf-8") == record.content
        assert second.content == download.content
        assert [s["key"] for s in deserialize_report(record.content)["sections"]] == (
            ROADMAP_SECTIONS
        )

    async def test_download_missing_artifact_returns_404(
        self, tmp_path: Path
    ):
        store = make_store(tmp_path)
        session = store.db
        install_overrides(make_case(), store, fixture_generator())
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                post = await client.post(
                    f"/api/v1/cases/{CASE_ID}/reports",
                    json={"report_type": "detailed", "format": "html"},
                )
                assert post.status_code == 202
                record = session.reports[0]
                Path(record.file_path).unlink()
                response = await client.get(
                    f"/api/v1/reports/{record.report_id}/download"
                )
        finally:
            cleanup_overrides()

        assert response.status_code == 404
        assert response.json()["detail"]["error"]["code"] == "REPORT_NOT_AVAILABLE"

    async def test_pdf_renderer_unavailable_returns_explicit_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        def _raise():
            raise ImportError("reportlab unavailable")

        monkeypatch.setattr(render_module, "_import_reportlab", _raise)

        store = make_store(tmp_path)
        session = store.db
        install_overrides(make_case(), store, fixture_generator())
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/cases/{CASE_ID}/reports",
                    json={"report_type": "detailed", "format": "pdf"},
                )
        finally:
            cleanup_overrides()

        assert response.status_code == 500
        error = response.json()["detail"]["error"]
        assert error["code"] == "PDF_RENDERER_UNAVAILABLE"
        assert "PDF rendering is unavailable" in error["message"]
        assert session.jobs[0].status == "failed"
        assert session.reports == []  # nothing fabricated when export fails
