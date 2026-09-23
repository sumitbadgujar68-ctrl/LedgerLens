from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.services.blockchain import BlockchainErrorCode, TransferCategory


class TraceParameters(BaseModel):
    direction: str = "outbound"
    max_hops: int = Field(default=3, ge=1, le=10)
    max_branches: int = Field(default=25, ge=1, le=500)
    min_amount: Optional[Decimal] = None
    asset_filters: Optional[List[str]] = None
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None


class TraceRequest(BaseModel):
    start_wallet_address: Optional[str] = Field(default=None, max_length=255)
    direction: str = Field(default="outbound", pattern="^(outbound|inbound|both)$")
    max_hops: int = Field(default=3, ge=1, le=10)
    max_branches: int = Field(default=25, ge=1, le=500)
    min_amount: Optional[Decimal] = Field(default=None, ge=0)
    asset_filters: Optional[List[str]] = None
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None


class CanonicalTransactionResponse(BaseModel):
    chain: str
    transaction_hash: str
    block_number: Optional[int] = None
    block_timestamp: Optional[datetime] = None
    from_address: str
    to_address: Optional[str] = None
    asset: Optional[str] = None
    asset_type: str
    amount: Decimal
    decimals: int
    token_contract: Optional[str] = None
    transfer_category: str
    transaction_type: str
    status: str
    gas_used: Optional[int] = None
    max_fee_per_gas: Optional[Decimal] = None
    priority_fee_per_gas: Optional[Decimal] = None
    total_fee: Optional[Decimal] = None
    provider: str
    provider_reference: str
    raw_reference: Optional[str] = None

    class Config:
        from_attributes = True


class GraphNodeResponse(BaseModel):
    id: str
    type: str
    label: Optional[str] = None
    hop: int = 0
    metadata: dict = Field(default_factory=dict)


class GraphEdgeResponse(BaseModel):
    id: str
    source: str
    target: str
    type: str
    transaction_hash: str
    amount: Decimal
    asset: Optional[str] = None
    timestamp: Optional[datetime] = None
    hop: int = 0


class GraphSummaryResponse(BaseModel):
    root_wallet_address: str
    blockchain: str
    node_count: int = 0
    edge_count: int = 0
    max_hop_depth: int = 0
    nodes: List[GraphNodeResponse] = Field(default_factory=list)
    edges: List[GraphEdgeResponse] = Field(default_factory=list)


class TraceSummaryResponse(BaseModel):
    wallet_count: int = 0
    transaction_count: int = 0
    edge_count: int = 0
    max_hop_depth: int = 0
    assets_transferred: dict = Field(default_factory=dict)
    pages_fetched: int = 0
    provider: Optional[str] = None


class TraceResponse(BaseModel):
    trace_id: UUID
    case_id: UUID
    status: str
    result_status: str
    start_wallet_address: str
    blockchain: str
    direction: str
    parameters: TraceParameters
    summary: TraceSummaryResponse
    transactions: List[CanonicalTransactionResponse] = Field(default_factory=list)
    graph: Optional[GraphSummaryResponse] = None
    errors: List[str] = Field(default_factory=list)
    provider: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ErrorResponse(BaseModel):
    error: dict
