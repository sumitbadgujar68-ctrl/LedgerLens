import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.copilot_schemas import (
    CopilotAskRequest,
    CopilotAskResponse,
    CopilotExplainRiskRequest,
    CopilotExplainRiskResponse,
    CopilotSummarizeResponse,
    ErrorResponse,
)
from app.services.ai.engine import (
    CaseNotFoundError,
    CopilotEngine,
    ProviderError,
    ProviderNotConfiguredError,
    get_copilot_engine,
)

logger = logging.getLogger("ledgerlens.api.copilot")

router = APIRouter(prefix="/cases", tags=["copilot"])


def _handle_engine_exceptions(case_id: UUID, e: Exception) -> None:
    if isinstance(e, CaseNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": str(e)}},
        )
    if isinstance(e, ProviderNotConfiguredError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": {"code": "PROVIDER_NOT_CONFIGURED", "message": str(e)}},
        )
    if isinstance(e, ProviderError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": {"code": "PROVIDER_ERROR", "message": str(e)}},
        )
    logger.exception(f"Copilot operation failed for case {case_id}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"error": {"code": "COPILOT_ERROR", "message": f"Copilot service error: {str(e)}"}},
    )


@router.post(
    "/{case_id}/copilot/ask",
    response_model=CopilotAskResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Case not found"},
        502: {"model": ErrorResponse, "description": "Provider error"},
        503: {"model": ErrorResponse, "description": "Provider not configured"},
        500: {"model": ErrorResponse, "description": "Unexpected error"},
    },
)
async def ask_copilot(
    case_id: UUID,
    request: CopilotAskRequest,
    trace_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    engine: CopilotEngine = Depends(get_copilot_engine),
):
    """
    Ask the AI copilot a question about the case.
    The copilot answers grounded in case data with citations.
    """
    try:
        result = await engine.ask(case_id, request.question, trace_id)
        return CopilotAskResponse(**result)
    except (CaseNotFoundError, ProviderNotConfiguredError, ProviderError) as e:
        _handle_engine_exceptions(case_id, e)
    except HTTPException:
        raise
    except Exception as e:
        _handle_engine_exceptions(case_id, e)


@router.post(
    "/{case_id}/copilot/summarize",
    response_model=CopilotSummarizeResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Case not found"},
        502: {"model": ErrorResponse, "description": "Provider error"},
        503: {"model": ErrorResponse, "description": "Provider not configured"},
        500: {"model": ErrorResponse, "description": "Unexpected error"},
    },
)
async def summarize_case(
    case_id: UUID,
    trace_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    engine: CopilotEngine = Depends(get_copilot_engine),
):
    """
    Generate a comprehensive summary of the case investigation.
    """
    try:
        result = await engine.summarize(case_id, trace_id)
        return CopilotSummarizeResponse(**result)
    except (CaseNotFoundError, ProviderNotConfiguredError, ProviderError) as e:
        _handle_engine_exceptions(case_id, e)
    except HTTPException:
        raise
    except Exception as e:
        _handle_engine_exceptions(case_id, e)


@router.post(
    "/{case_id}/copilot/explain_risk",
    response_model=CopilotExplainRiskResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Case not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        502: {"model": ErrorResponse, "description": "Provider error"},
        503: {"model": ErrorResponse, "description": "Provider not configured"},
        500: {"model": ErrorResponse, "description": "Unexpected error"},
    },
)
async def explain_risk(
    case_id: UUID,
    request: CopilotExplainRiskRequest,
    db: AsyncSession = Depends(get_db),
    engine: CopilotEngine = Depends(get_copilot_engine),
):
    """
    Explain the risk score for a specific wallet in the case.
    """
    try:
        result = await engine.explain_risk(case_id, request.wallet_address, request.trace_id)
        return CopilotExplainRiskResponse(**result)
    except (CaseNotFoundError, ProviderNotConfiguredError, ProviderError) as e:
        _handle_engine_exceptions(case_id, e)
    except HTTPException:
        raise
    except Exception as e:
        _handle_engine_exceptions(case_id, e)
