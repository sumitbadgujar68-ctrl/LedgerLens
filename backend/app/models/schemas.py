from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID

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
