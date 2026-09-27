from pydantic import BaseModel, Field, EmailStr, model_validator
from typing import Optional, Any, Dict
from datetime import datetime
from decimal import Decimal
from uuid import UUID

DEMO_META_MARKER = "demo_data"
DEMO_META_PREFIX = "{"


def parse_demo_meta(notes: Optional[str]) -> Dict[str, Any]:
    """Extract the demo metadata header from a case's investigator_notes.

    Demo rows carry a JSON header object on the first line of investigator_notes,
    e.g. {"demo_data": true, "case_type": "MVP_DEMO", ...} followed by a free-text
    description. Returns {} when the notes are absent or not demo metadata.
    """
    if not notes:
        return {}
    first_line = notes.strip().splitlines()[0].strip() if notes.strip() else ""
    if not first_line.startswith(DEMO_META_PREFIX):
        return {}
    try:
        import json

        parsed = json.loads(first_line)
    except (ValueError, TypeError):
        return {}
    if not isinstance(parsed, dict) or DEMO_META_MARKER not in parsed:
        return {}
    return parsed

class CaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    reported_wallet_address: str = Field(..., min_length=1, max_length=255)
    reported_transaction_hash: Optional[str] = Field(None, max_length=255)
    blockchain: str = Field(..., pattern="^(ethereum|tron|bitcoin|solana)$")
    fraud_type: str = Field(..., 
        pattern="^(investment_scam|ransomware|sextortion|phishing|task_based_fraud|darknet|other)$")
    reported_amount: Optional[Decimal] = None
    reported_asset: Optional[str] = Field(None, max_length=50)
    reported_date: Optional[datetime] = None
    investigator_notes: Optional[str] = None

class CaseResponse(BaseModel):
    case_id: UUID
    case_number: str
    title: str
    reported_wallet_address: str
    reported_transaction_hash: Optional[str]
    blockchain: str
    fraud_type: str
    reported_amount: Optional[Decimal]
    reported_asset: Optional[str]
    reported_date: Optional[datetime]
    status: str
    investigator_id: UUID
    investigator_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    demo_data: bool = False
    data_source: Optional[str] = None

    @model_validator(mode="after")
    def _derive_demo_flags(self) -> "CaseResponse":
        meta = parse_demo_meta(self.investigator_notes)
        self.demo_data = bool(meta.get("demo_data", False))
        self.data_source = meta.get("data_source")
        return self

    class Config:
        from_attributes = True

class CaseUpdate(BaseModel):
    status: Optional[str] = Field(None, 
        pattern="^(active|under_investigation|closed|archived)$")
    investigator_notes: Optional[str] = None

class InvestigatorCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="investigator", pattern="^(admin|investigator|viewer)$")

class InvestigatorResponse(BaseModel):
    investigator_id: UUID
    username: str
    email: str
    full_name: str
    role: str
    active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

class ErrorResponse(BaseModel):
    error: dict
