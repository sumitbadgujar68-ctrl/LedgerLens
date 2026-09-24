from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CitationResponse(BaseModel):
    type: str
    reference_id: str
    summary: str
    detail: Optional[str] = None
    confidence: float = 1.0


class CopilotAskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class CopilotAskResponse(BaseModel):
    answer: str
    citations: List[CitationResponse] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    type: str


class CopilotSummarizeResponse(BaseModel):
    answer: str
    citations: List[CitationResponse] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    type: str


class CopilotExplainRiskRequest(BaseModel):
    wallet_address: str = Field(..., min_length=42, max_length=42)
    trace_id: Optional[UUID] = None


class CopilotExplainRiskResponse(BaseModel):
    answer: str
    citations: List[CitationResponse] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    type: str


class ErrorResponse(BaseModel):
    error: Dict[str, Any]