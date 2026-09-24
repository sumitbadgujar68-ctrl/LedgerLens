"""Phase 6 — report API endpoints (docs/API_CONTRACT.md section 4.9).

POST /api/v1/cases/{case_id}/reports   — enqueue report generation (202)
GET  /api/v1/cases/{case_id}/reports   — list case reports (200)
GET  /api/v1/reports/{report_id}/download — download persisted report (200)

Conventions follow the existing routers (cases.py, traces.py, copilot.py):
CASE_NOT_FOUND-style error envelopes, Depends(get_db), injected store and
generator providers, and synchronous in-request generation as in traces.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.cases import MOCK_INVESTIGATOR_ID
from app.db.database import get_db
from app.models.report_schemas import (
    ErrorResponse,
    ReportGenerateRequest,
    ReportJobQueuedResponse,
    ReportListItemResponse,
    ReportListResponse,
)
from app.services.case_service import CaseService
from app.services.reporting import (
    MEDIA_TYPES as DOWNLOAD_MEDIA_TYPES,
)
from app.services.reporting import (
    InvalidReportTypeError,
    PdfRendererUnavailableError,
    ReportArtifactNotFoundError,
    ReportCaseNotFoundError,
    ReportGenerator,
    ReportStore,
    get_report_store,
)

logger = logging.getLogger("ledgerlens.api.reports")

router = APIRouter(tags=["reports"])


def get_report_generator(db: AsyncSession = Depends(get_db)) -> ReportGenerator:
    return ReportGenerator(db)


def _case_not_found(case_id: UUID) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": {"code": "CASE_NOT_FOUND", "message": f"Case {case_id} not found"}},
    )


@router.post(
    "/cases/{case_id}/reports",
    response_model=ReportJobQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        404: {"model": ErrorResponse, "description": "Case not found"},
        422: {"model": ErrorResponse, "description": "Invalid report type or format"},
        500: {"model": ErrorResponse, "description": "Report generation error"},
    },
)
async def create_report(
    case_id: UUID,
    request: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    store: ReportStore = Depends(get_report_store),
    generator: ReportGenerator = Depends(get_report_generator),
):
    """Generate an investigation report for a case and queue the job."""
    case = await CaseService.get_case(db, case_id)
    if not case:
        raise _case_not_found(case_id)

    job = await store.create_job(
        case_id, request.report_type, request.format, MOCK_INVESTIGATOR_ID
    )
    await store.mark_job_started(job)
    try:
        report = await generator.generate(
            case_id,
            request.report_type,
            request.format,
            generated_by=MOCK_INVESTIGATOR_ID,
        )
        record = await store.save_report(report, MOCK_INVESTIGATOR_ID)
        await store.mark_job_completed(job, result={"report_id": str(record.report_id)})
        await db.commit()
    except ReportCaseNotFoundError as e:
        await store.mark_job_failed(job, str(e))
        await db.commit()
        raise _case_not_found(case_id)
    except InvalidReportTypeError as e:
        await store.mark_job_failed(job, str(e))
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": {"code": "INVALID_REPORT_TYPE", "message": str(e)}},
        )
    except HTTPException:
        raise
    except PdfRendererUnavailableError as e:
        logger.error("PDF renderer unavailable for case %s: %s", case_id, e)
        await store.mark_job_failed(job, str(e))
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "PDF_RENDERER_UNAVAILABLE",
                    "message": str(e),
                }
            },
        )
    except Exception as e:
        logger.exception("Report generation failed for case %s", case_id)
        await store.mark_job_failed(job, str(e))
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "REPORT_GENERATION_ERROR",
                    "message": f"Report generation failed: {e}",
                }
            },
        )
    return ReportJobQueuedResponse(job_id=job.job_id)


@router.get(
    "/cases/{case_id}/reports",
    response_model=ReportListResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Case not found"},
    },
)
async def list_reports(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    store: ReportStore = Depends(get_report_store),
):
    """List all reports for a case, newest first."""
    case = await CaseService.get_case(db, case_id)
    if not case:
        raise _case_not_found(case_id)

    records = await store.get_reports_for_case(case_id)
    items = [
        ReportListItemResponse(
            report_id=record.report_id,
            report_type=record.report_type,
            format=record.format,
            generated_at=record.generated_at,
            file_url=f"/api/v1/reports/{record.report_id}/download",
        )
        for record in records
    ]
    return ReportListResponse(reports=items)


@router.get(
    "/reports/{report_id}/download",
    response_class=Response,
    responses={
        200: {"content": {"application/octet-stream": {}}, "description": "Report file"},
        404: {"model": ErrorResponse, "description": "Report not found"},
    },
)
async def download_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    store: ReportStore = Depends(get_report_store),
):
    """Download the persisted report exactly as stored (no regeneration)."""
    record = await store.get_report(report_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "REPORT_NOT_FOUND", "message": f"Report {report_id} not found"}},
        )
    if record.content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "REPORT_NOT_AVAILABLE",
                    "message": f"Report {report_id} has no generated content",
                }
            },
        )

    case = await CaseService.get_case(db, record.case_id)
    case_number = case.case_number if case else str(record.report_id)
    filename = f"{case_number}_report.{record.format}"
    media_type = DOWNLOAD_MEDIA_TYPES.get(record.format, "application/octet-stream")
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}

    if record.file_path:
        # HTML/PDF artifacts were rendered once at save time; serve them
        # verbatim instead of re-rendering the persisted report data.
        try:
            payload = store.read_artifact(record)
        except ReportArtifactNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "REPORT_NOT_AVAILABLE",
                        "message": (
                            f"Report {report_id} export artifact is not available"
                        ),
                    }
                },
            )
        return Response(content=payload, media_type=media_type, headers=headers)

    if record.format in ("html", "pdf"):
        # Documented export format without a persisted artifact: never
        # regenerate report content during download.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "REPORT_NOT_AVAILABLE",
                    "message": f"Report {report_id} has no stored export artifact",
                }
            },
        )

    return Response(content=record.content, media_type=media_type, headers=headers)
