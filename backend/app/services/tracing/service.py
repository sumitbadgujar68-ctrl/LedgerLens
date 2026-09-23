import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Case, GraphRecord, TraceRun, TransactionRecord
from app.services.blockchain import BlockchainAdapter, BlockchainErrorCode, TransferDirection
from app.services.graph.model import TraceConfig
from app.services.tracing.tracer import TraceOutcome, run_bounded_trace

logger = logging.getLogger("ledgerlens.tracing.service")


class TraceService:
    def __init__(self, adapter: BlockchainAdapter) -> None:
        self._adapter = adapter

    async def get_case(self, db: AsyncSession, case_id: UUID) -> Optional[Case]:
        result = await db.execute(select(Case).where(Case.case_id == case_id))
        return result.scalar_one_or_none()

    async def get_trace(self, db: AsyncSession, case_id: UUID, trace_id: UUID) -> Optional[TraceRun]:
        result = await db.execute(
            select(TraceRun).where(TraceRun.case_id == case_id, TraceRun.trace_id == trace_id)
        )
        return result.scalar_one_or_none()

    async def list_traces(self, db: AsyncSession, case_id: UUID, limit: int = 20) -> List[TraceRun]:
        result = await db.execute(
            select(TraceRun)
            .where(TraceRun.case_id == case_id)
            .order_by(TraceRun.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def execute_trace(
        self,
        db: AsyncSession,
        case: Case,
        start_wallet: Optional[str] = None,
        direction: TransferDirection = TransferDirection.OUTBOUND,
        config: Optional[TraceConfig] = None,
    ) -> TraceRun:
        config = config or TraceConfig()
        wallet = (start_wallet or case.reported_wallet_address).strip()
        direction_value = direction.value if isinstance(direction, TransferDirection) else str(direction)

        trace = TraceRun(
            trace_id=uuid.uuid4(),
            case_id=case.case_id,
            start_wallet_address=wallet.lower(),
            blockchain=case.blockchain,
            direction=direction_value,
            max_hops=config.max_hops,
            max_branches=config.max_branches,
            min_amount=config.min_amount,
            asset_filters=config.asset_filters,
            time_range_start=config.time_range_start,
            time_range_end=config.time_range_end,
            status="running",
            parameters={
                "direction": direction_value,
                "max_hops": config.max_hops,
                "max_branches": config.max_branches,
                "min_amount": str(config.min_amount) if config.min_amount is not None else None,
                "asset_filters": config.asset_filters,
                "time_range_start": config.time_range_start.isoformat() if config.time_range_start else None,
                "time_range_end": config.time_range_end.isoformat() if config.time_range_end else None,
            },
            summary={},
            errors=[],
        )
        db.add(trace)
        await db.flush()

        try:
            outcome = await run_bounded_trace(
                adapter=self._adapter,
                start_wallet=wallet,
                config=config,
                direction=direction if isinstance(direction, TransferDirection) else TransferDirection(direction_value),
                chain=case.blockchain,
            )
        except Exception as exc:  # noqa: BLE001 - convert to failed trace status
            logger.exception("trace failed case=%s", case.case_id)
            trace.status = "failed"
            trace.result_status = BlockchainErrorCode.FAILED.value
            trace.provider = self._adapter.provider_name
            trace.errors = [f"trace_failed: {exc}"]
            trace.summary = {}
            trace.completed_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(trace)
            return trace

        await self._persist_outcome(db, case, trace, outcome)
        await db.commit()
        await db.refresh(trace)
        return trace

    async def _persist_outcome(
        self,
        db: AsyncSession,
        case: Case,
        trace: TraceRun,
        outcome: TraceOutcome,
    ) -> None:
        status_map = {
            BlockchainErrorCode.SUCCESS: "completed",
            BlockchainErrorCode.NO_DATA: "completed",
            BlockchainErrorCode.PARTIAL_SUCCESS: "partial",
            BlockchainErrorCode.FAILED: "failed",
            BlockchainErrorCode.RATE_LIMITED: "failed",
            BlockchainErrorCode.PROVIDER_UNAVAILABLE: "failed",
            BlockchainErrorCode.INVALID_INPUT: "failed",
        }
        trace.status = status_map.get(outcome.status, "failed")
        trace.result_status = outcome.status.value
        trace.provider = outcome.provider
        trace.summary = outcome.summary
        trace.errors = outcome.errors
        trace.completed_at = datetime.now(timezone.utc)

        for tx in outcome.transactions:
            hop = _discover_hop(outcome, tx)
            db.add(
                TransactionRecord(
                    case_id=case.case_id,
                    trace_id=trace.trace_id,
                    transaction_hash=tx.transaction_hash,
                    blockchain=tx.chain,
                    block_number=tx.block_number,
                    block_timestamp=tx.block_timestamp,
                    from_address=tx.from_address,
                    to_address=tx.to_address,
                    asset_symbol=tx.asset,
                    asset_type=tx.asset_type.value if tx.asset_type else None,
                    amount=tx.amount,
                    decimals=tx.decimals,
                    token_contract_address=tx.token_contract,
                    transfer_category=tx.transfer_category.value if tx.transfer_category else None,
                    transaction_type=tx.transaction_type.value if tx.transaction_type else "transfer",
                    status=tx.status.value if tx.status else "unknown",
                    gas_used=tx.gas_used,
                    max_fee_per_gas=tx.max_fee_per_gas,
                    priority_fee_per_gas=tx.priority_fee_per_gas,
                    total_fee=tx.total_fee,
                    provider_source=tx.provider,
                    provider_reference=tx.provider_reference,
                    raw_reference=tx.raw_reference,
                    discovered_at_hop=hop,
                )
            )

        graph_payload = {
            "root_wallet_address": outcome.graph.root_wallet_address,
            "blockchain": outcome.graph.blockchain,
            "nodes": [n.model_dump(mode="json") for n in outcome.graph.nodes],
            "edges": [
                {**e.model_dump(mode="json"), "amount": str(e.amount)}
                for e in outcome.graph.edges
            ],
            "node_count": outcome.graph.node_count,
            "edge_count": outcome.graph.edge_count,
            "max_hop_depth": outcome.graph.max_hop_depth,
        }
        db.add(
            GraphRecord(
                case_id=case.case_id,
                trace_id=trace.trace_id,
                root_wallet_address=outcome.graph.root_wallet_address,
                blockchain=outcome.graph.blockchain,
                max_hop_depth=outcome.graph.max_hop_depth,
                branch_limit=trace.max_branches,
                dust_threshold=trace.min_amount,
                time_window_start=trace.time_range_start,
                time_window_end=trace.time_range_end,
                node_count=outcome.graph.node_count,
                edge_count=outcome.graph.edge_count,
                graph_data=graph_payload,
            )
        )


def _discover_hop(outcome: TraceOutcome, tx) -> int:
    root = outcome.graph.root_wallet_address
    best = 0
    for edge in outcome.graph.edges:
        if edge.transaction_hash == tx.transaction_hash and (
            edge.source == root or edge.target == root
        ):
            best = max(best, edge.hop)
            break
    for edge in outcome.graph.edges:
        if edge.transaction_hash == tx.transaction_hash:
            best = max(best, min(edge.hop, outcome.graph.max_hop_depth or edge.hop))
    return max(best - 1 if best > 0 else 0, 0)
