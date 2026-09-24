from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# Documented enums (docs/DATA_MODEL.md 4.13; docs/API_CONTRACT.md 4.9).
REPORT_TYPES = ("summary", "detailed", "evidence_export")
REPORT_FORMATS = ("pdf", "json", "html")


class ErrorResponse(BaseModel):
    error: Dict[str, Any]


class ReportGenerateRequest(BaseModel):
    """POST /cases/{case_id}/reports request body (API_CONTRACT.md 4.9)."""

    report_type: str
    format: str

    @field_validator("report_type")
    @classmethod
    def validate_report_type(cls, value: str) -> str:
        if value not in REPORT_TYPES:
            raise ValueError(
                f"report_type must be one of: {', '.join(REPORT_TYPES)}"
            )
        return value

    @field_validator("format")
    @classmethod
    def validate_format(cls, value: str) -> str:
        if value not in REPORT_FORMATS:
            raise ValueError(
                f"format must be one of: {', '.join(REPORT_FORMATS)}"
            )
        return value


class ReportJobQueuedResponse(BaseModel):
    """202 Accepted response for queued report generation (API_CONTRACT.md 4.9)."""

    job_id: UUID
    status: str = "queued"
    message: str = "Report generation job queued"


class ReportListItemResponse(BaseModel):
    """Report entry in GET /cases/{case_id}/reports (API_CONTRACT.md 4.9)."""

    report_id: UUID
    report_type: str
    format: str
    generated_at: datetime
    file_url: str


class ReportListResponse(BaseModel):
    reports: List[ReportListItemResponse] = Field(default_factory=list)


class ReportMetadataResponse(BaseModel):
    """GET /reports/{report_id} metadata (ROADMAP.md Phase 6 API surface)."""

    report_id: UUID
    report_type: str
    format: str
    generated_at: datetime
    file_url: str


class ReportSectionResponse(BaseModel):
    """Uniform report section envelope (14 documented sections, ROADMAP.md 764-778).

    Unavailable sources carry available=false plus a reason; empty findings
    carry available=true plus data counts — unavailable-data semantics are
    preserved verbatim through serialization.
    """

    key: str
    title: str
    available: bool
    data: Optional[Any] = None
    reason: Optional[str] = None
    note: Optional[str] = None


class ReportDataResponse(BaseModel):
    """Structured report data as produced by ReportGenerator (Step 1 contract).

    Sections retain every provenance identifier (transaction_hash, pattern_id,
    attribution_id, risk_score_id, evidence_id, trace_id) inside data, which
    is carried through unchanged as Any.
    """

    case_id: str
    case_number: Optional[str] = None
    title: Optional[str] = None
    report_type: str
    format: str
    generated_at: str
    generated_by: Optional[str] = None
    sections: List[ReportSectionResponse]
    unavailable_sections: List[str]
