"""Phase 6 — report persistence layer.

Stores ReportGenerator output as deterministic JSON in reports.content,
tracks report-generation jobs per docs/DATA_MODEL.md sections 4.13-4.14,
and provides read accessors for the Phase 6 report endpoints.

Guarantees:
- Deterministic serialization: sorted keys, stable separators — identical
  report data always produces identical stored content.
- Round-trip fidelity: deserialize(serialize(report)) == report, preserving
  every provenance identifier and unavailable-data flag verbatim.
- Validation: report_type/format are checked against the documented enums
  before anything is persisted; nothing undocumented is written.
- Artifact export (Step 5): HTML/PDF reports are rendered once at save time
  into an artifact file and reports.file_path records it, so the download
  endpoint serves the persisted artifact without regenerating the report.
  JSON reports stay inline (file_path remains None).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from sqlalchemy import select
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import JobRecord, ReportRecord
from app.services.reporting.artifacts import (
    ReportArtifactNotFoundError,
    ReportArtifactStore,
    get_report_artifact_store,
)
from app.services.reporting.generator import (
    VALID_FORMATS,
    VALID_REPORT_TYPES,
    InvalidReportTypeError,
)
from app.services.reporting.render import (
    ARTIFACT_FORMATS,
    deserialize_report,
    serialize_report,
)

REPORT_GENERATION_JOB_TYPE = "report_generation"


class ReportStore:
    """Read/write access for reports and report-generation jobs.

    Read-only with respect to case/trace/graph/risk data: only the reports
    and jobs tables are ever written.
    """

    def __init__(
        self, db, artifacts: Optional[ReportArtifactStore] = None
    ) -> None:
        self.db = db
        self.artifacts = (
            artifacts if artifacts is not None else get_report_artifact_store()
        )

    # ------------------------------------------------------------------
    # Job lifecycle (job_type = report_generation)
    # ------------------------------------------------------------------

    async def create_job(
        self,
        case_id: Union[UUID, str],
        report_type: str,
        report_format: str,
        initiated_by: Union[UUID, str],
        extra_parameters: Optional[Dict[str, Any]] = None,
    ) -> JobRecord:
        """Create a queued report-generation job (API_CONTRACT.md 4.9 202)."""
        self._validate_report_type(report_type)
        self._validate_format(report_format)
        if initiated_by is None:
            raise ValueError("initiated_by is required (jobs.initiated_by is NOT NULL)")

        parameters: Dict[str, Any] = {
            "report_type": report_type,
            "format": report_format,
        }
        if extra_parameters:
            parameters.update(extra_parameters)

        record = JobRecord(
            job_type=REPORT_GENERATION_JOB_TYPE,
            status="queued",
            progress=0,
            case_id=UUID(str(case_id)),
            initiated_by=UUID(str(initiated_by)),
            parameters=parameters,
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def mark_job_started(self, job: JobRecord) -> JobRecord:
        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        await self.db.flush()
        return job

    async def mark_job_completed(
        self, job: JobRecord, result: Optional[Dict[str, Any]] = None
    ) -> JobRecord:
        job.status = "completed"
        job.progress = 100
        job.result = result or {}
        job.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return job

    async def mark_job_failed(self, job: JobRecord, error_message: str) -> JobRecord:
        job.status = "failed"
        job.error_message = error_message
        job.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return job

    async def get_job(self, job_id: Union[UUID, str]) -> Optional[JobRecord]:
        result = await self.db.execute(
            select(JobRecord).where(JobRecord.job_id == UUID(str(job_id)))
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Report storage
    # ------------------------------------------------------------------

    async def save_report(
        self,
        report: Dict[str, Any],
        generated_by: Union[UUID, str],
    ) -> ReportRecord:
        """Persist ReportGenerator output as a reports row.

        The stored content is the deterministic serialization of the exact
        report dict; generated_at is taken from the report itself so the
        record and its content can never disagree.
        """
        report_type = report.get("report_type")
        report_format = report.get("format")
        self._validate_report_type(report_type)
        self._validate_format(report_format)
        if not generated_by:
            raise ValueError(
                "generated_by is required (reports.generated_by is NOT NULL)"
            )

        generated_at: Optional[datetime] = None
        raw_generated_at = report.get("generated_at")
        if raw_generated_at:
            generated_at = datetime.fromisoformat(str(raw_generated_at))

        record = ReportRecord(
            report_id=uuid4(),
            case_id=UUID(str(report.get("case_id"))),
            report_type=report_type,
            format=report_format,
            content=serialize_report(report),
            file_path=None,
            generated_by=UUID(str(generated_by)),
        )
        if generated_at is not None:
            record.generated_at = generated_at

        if report_format in ARTIFACT_FORMATS:
            record.file_path = self.artifacts.write(report, record.report_id)

        self.db.add(record)
        await self.db.flush()
        return record

    def read_artifact(self, report: ReportRecord) -> bytes:
        """Read the persisted artifact bytes for a rendered report.

        Raises ReportArtifactNotFoundError when no artifact was persisted or
        the file is no longer available — the caller must not re-render.
        """
        if not report.file_path:
            raise ReportArtifactNotFoundError(
                f"Report {report.report_id} has no stored artifact file"
            )
        return self.artifacts.read(report.file_path)

    async def get_report(self, report_id: Union[UUID, str]) -> Optional[ReportRecord]:
        result = await self.db.execute(
            select(ReportRecord).where(ReportRecord.report_id == UUID(str(report_id)))
        )
        return result.scalar_one_or_none()

    async def get_reports_for_case(
        self, case_id: Union[UUID, str]
    ) -> List[ReportRecord]:
        """List a case's reports, newest first (documented list order)."""
        result = await self.db.execute(
            select(ReportRecord)
            .where(ReportRecord.case_id == UUID(str(case_id)))
            .order_by(ReportRecord.generated_at.desc())
        )
        return list(result.scalars().all())

    def get_report_data(self, report: ReportRecord) -> Dict[str, Any]:
        """Deserialize stored report content back to structured report data."""
        if report.content is None:
            raise ValueError("Report content is not stored")
        return deserialize_report(report.content)

    # ------------------------------------------------------------------
    # Validation helpers (documented enums only)
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_report_type(report_type: Any) -> None:
        if report_type not in VALID_REPORT_TYPES:
            raise InvalidReportTypeError(
                f"Invalid report type {report_type!r}; "
                f"expected one of {', '.join(VALID_REPORT_TYPES)}"
            )

    @staticmethod
    def _validate_format(report_format: Any) -> None:
        if report_format not in VALID_FORMATS:
            raise InvalidReportTypeError(
                f"Invalid report format {report_format!r}; "
                f"expected one of {', '.join(VALID_FORMATS)}"
            )


def get_report_store(db: AsyncSession = Depends(get_db)) -> ReportStore:
    return ReportStore(db)
