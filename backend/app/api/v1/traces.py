import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.database import get_db
from app.models.trace_schemas import (
    CanonicalTransactionResponse,
    ErrorResponse,
    GraphEdgeResponse,
    GraphNodeResponse,
    GraphSummaryResponse,
    TraceParameters,
    TraceRequest,
    TraceResponse,
    TraceSummaryResponse,
)
from app.services.auth.deps import (
    Principal,
    get_current_principal,
    require_case_ownership,
)
from app.services.blockchain import BlockchainAdapter, TransferDirection, TransferQuery
from app.services.graph.model import TraceConfig
from app.services.tracing.service import TraceService

logger = logging.getLogger("ledgerlens.api.traces")

router = APIRouter(prefix="/cases", tags=["traces"])


def get_blockchain_adapter() -> BlockchainAdapter:
    from app.config import settings
    from app.services.blockchain import AlchemyProvider, EthereumAdapter
    from app.services.blockchain import BlockchainErrorCode, TransferFetchResult

    api_key = settings.alchemy_api_key
    if not api_key:
        class UnconfiguredAdapter(BlockchainAdapter):
            provider_name = "alchemy"

            def validate_address(self, address: str) -> str:
                return (address or "").strip().lower()

            async def fetch_transfers(self, query: TransferQuery) -> TransferFetchResult:
                return TransferFetchResult(
                    status=BlockchainErrorCode.PROVIDER_UNAVAILABLE,
                    transactions=[],
                    provider=self.provider_name,
                    errors=["ALCHEMY_API_KEY is not configured"],
                )

        return UnconfiguredAdapter()
    return EthereumAdapter(
        provider=AlchemyProvider(api_key=api_key, network=settings.alchemy_network)
    )


def get_trace_service(adapter: BlockchainAdapter = Depends(get_blockchain_adapter)) -> TraceService:
    return TraceService(adapter)


def _build_response(trace, transactions=None, graph_payload=None) -> TraceResponse:
    parameters = TraceParameters(
        direction=trace.direction,
        max_hops=trace.max_hops,
        max_branches=trace.max_branches,
        min_amount=trace.min_amount,
        asset_filters=trace.asset_filters,
        time_range_start=trace.time_range_start,
        time_range_end=trace.time_range_end,
    )
    summary_raw = trace.summary or {}
    summary = TraceSummaryResponse(
        wallet_count=int(summary_raw.get("wallet_count", 0)),
        transaction_count=int(summary_raw.get("transaction_count", 0)),
        edge_count=int(summary_raw.get("edge_count", 0)),
        max_hop_depth=int(summary_raw.get("max_hop_depth", 0)),
        assets_transferred=summary_raw.get("assets_transferred", {}),
        pages_fetched=int(summary_raw.get("pages_fetched", 0)),
        provider=summary_raw.get("provider") or trace.provider,
    )

    tx_list = transactions if transactions is not None else []
    graph = None
    if graph_payload:
        graph = GraphSummaryResponse(
            root_wallet_address=graph_payload.get("root_wallet_address", trace.start_wallet_address),
            blockchain=graph_payload.get("blockchain", trace.blockchain),
            node_count=int(graph_payload.get("node_count", 0)),
            edge_count=int(graph_payload.get("edge_count", 0)),
            max_hop_depth=int(graph_payload.get("max_hop_depth", 0)),
            nodes=[GraphNodeResponse(**n) for n in graph_payload.get("nodes", [])],
            edges=[GraphEdgeResponse(**e) for e in graph_payload.get("edges", [])],
        )

    return TraceResponse(
        trace_id=trace.trace_id,
        case_id=trace.case_id,
        status=trace.status,
        result_status=trace.result_status or "",
        start_wallet_address=trace.start_wallet_address,
        blockchain=trace.blockchain,
        direction=trace.direction,
        parameters=parameters,
        summary=summary,
        transactions=tx_list,
        graph=graph,
        errors=list(trace.errors or []),
        provider=trace.provider,
        created_at=trace.created_at,
        completed_at=trace.completed_at,
    )


async def _load_trace_payload(db: AsyncSession, trace):
    from sqlalchemy import select
    from app.db.models import GraphRecord, TransactionRecord
    from app.services.blockchain import (
        AssetType,
        CanonicalTransaction,
        TransactionStatus,
        TransactionType,
        TransferCategory,
    )

    tx_rows = (
        (
            await db.execute(
                select(TransactionRecord)
                .where(TransactionRecord.trace_id == trace.trace_id)
                .order_by(
                    TransactionRecord.block_number.asc().nulls_last(),
                    TransactionRecord.transaction_hash.asc(),
                )
            )
        )
        .scalars()
        .all()
    )
    transactions = [
        CanonicalTransaction(
            chain=row.blockchain,
            transaction_hash=row.transaction_hash,
            block_number=row.block_number,
            block_timestamp=row.block_timestamp,
            from_address=row.from_address,
            to_address=row.to_address,
            asset=row.asset_symbol,
            asset_type=AssetType(row.asset_type) if row.asset_type else AssetType.UNKNOWN,
            amount=row.amount,
            decimals=row.decimals,
            token_contract=row.token_contract_address,
            transfer_category=TransferCategory(row.transfer_category)
            if row.transfer_category
            else TransferCategory.UNKNOWN,
            transaction_type=TransactionType(row.transaction_type)
            if row.transaction_type
            else TransactionType.UNKNOWN,
            status=TransactionStatus(row.status) if row.status else TransactionStatus.UNKNOWN,
            gas_used=row.gas_used,
            max_fee_per_gas=row.max_fee_per_gas,
            priority_fee_per_gas=row.priority_fee_per_gas,
            total_fee=row.total_fee,
            provider=row.provider_source,
            provider_reference=row.provider_reference,
            raw_reference=row.raw_reference,
        )
        for row in tx_rows
    ]

    graph_row = (
        await db.execute(select(GraphRecord).where(GraphRecord.trace_id == trace.trace_id))
    ).scalar_one_or_none()
    graph_payload = graph_row.graph_data if graph_row else None
    return transactions, graph_payload


@router.post(
    "/{case_id}/traces",
    response_model=TraceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_trace(
    case_id: UUID,
    request: Optional[TraceRequest] = None,
    db: AsyncSession = Depends(get_db),
    service: TraceService = Depends(get_trace_service),
    principal: Principal = Depends(get_current_principal),
):
    case = await service.get_case(db, case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": f"Case {case_id} not found"}},
        )
    require_case_ownership(case, principal, case_id)

    body = request or TraceRequest()
    if body.start_wallet_address is None:
        body.start_wallet_address = case.reported_wallet_address

    config = TraceConfig(
        max_hops=body.max_hops,
        max_branches=body.max_branches,
        min_amount=body.min_amount,
        asset_filters=body.asset_filters,
        time_range_start=body.time_range_start,
        time_range_end=body.time_range_end,
    )
    direction = TransferDirection(body.direction)

    trace = await service.execute_trace(
        db=db,
        case=case,
        start_wallet=body.start_wallet_address,
        direction=direction,
        config=config,
    )
    transactions, graph_payload = await _load_trace_payload(db, trace)
    return _build_response(trace, transactions, graph_payload)


@router.get("/{case_id}/traces/{trace_id}", response_model=TraceResponse)
async def get_trace(
    case_id: UUID,
    trace_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: TraceService = Depends(get_trace_service),
    principal: Principal = Depends(get_current_principal),
):
    case = await service.get_case(db, case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": f"Case {case_id} not found"}},
        )
    require_case_ownership(case, principal, case_id)
    trace = await service.get_trace(db, case_id, trace_id)
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TRACE_NOT_FOUND", "message": f"Trace {trace_id} not found"}},
        )
    transactions, graph_payload = await _load_trace_payload(db, trace)
    return _build_response(trace, transactions, graph_payload)


@router.get("/{case_id}/traces", response_model=list[TraceResponse])
async def list_traces(
    case_id: UUID,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    service: TraceService = Depends(get_trace_service),
    principal: Principal = Depends(get_current_principal),
):
    case = await service.get_case(db, case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CASE_NOT_FOUND", "message": f"Case {case_id} not found"}},
        )
    require_case_ownership(case, principal, case_id)
    traces = await service.list_traces(db, case_id, limit=limit)
    responses = []
    for trace in traces:
        transactions, graph_payload = await _load_trace_payload(db, trace)
        responses.append(_build_response(trace, transactions, graph_payload))
    return responses
