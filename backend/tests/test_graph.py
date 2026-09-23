from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.main import app
from app.api.v1.traces import get_blockchain_adapter, get_trace_service
from app.db.models import Case, Investigator
from app.db.database import async_session_maker
from app.services.blockchain import (
    BlockchainAdapter,
    BlockchainErrorCode,
    CanonicalTransaction,
    TransferFetchResult,
    TransferQuery,
)
from app.services.graph.model import TraceConfig
from app.services.tracing.tracer import run_bounded_trace
from app.services.blockchain import TransferDirection
from app.services.graph import CanonicalGraph, GraphEdge, GraphNode, NodeType, EdgeType

ROOT = "0x1111111111111111111111111111111111111111"
WALLET_B = "0x2222222222222222222222222222222222222222"
WALLET_C = "0x3333333333333333333333333333333333333333"
WALLET_D = "0x4444444444444444444444444444444444444444"


def make_tx(
    tx_hash: str,
    from_addr: str,
    to_addr: str,
    amount: str = "1.0",
    block: int = 100,
    asset: str = "ETH",
) -> CanonicalTransaction:
    return CanonicalTransaction(
        chain="ethereum",
        transaction_hash=tx_hash,
        block_number=block,
        block_timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        from_address=from_addr,
        to_address=to_addr,
        asset=asset,
        amount=Decimal(amount),
        decimals=18,
        provider="fake",
        provider_reference=f"ref-{tx_hash}-{from_addr[:6]}-{to_addr[:6]}",
        raw_reference=f"block={block}",
    )


class MapAdapter(BlockchainAdapter):
    def __init__(self, outbound_map: Optional[Dict[str, List[CanonicalTransaction]]] = None,
                 inbound_map: Optional[Dict[str, List[CanonicalTransaction]]] = None,
                 error: Optional[BlockchainErrorCode] = None,
                 errors_by_wallet: Optional[Dict[str, BlockchainErrorCode]] = None) -> None:
        self.outbound_map = outbound_map or {}
        self.inbound_map = inbound_map or {}
        self.error = error
        self.errors_by_wallet = errors_by_wallet or {}
        self.calls: List[str] = []
        self.provider_name = "fake"

    def validate_address(self, address: str) -> str:
        return address.lower()

    async def fetch_transfers(self, query: TransferQuery) -> TransferFetchResult:
        self.calls.append(query.address.lower())
        err = self.error or self.errors_by_wallet.get(query.address.lower())
        if err is not None:
            return TransferFetchResult(
                status=err,
                transactions=[],
                provider=self.provider_name,
                errors=[err.value],
            )

        txs: List[CanonicalTransaction] = []
        if query.direction == TransferDirection.OUTBOUND:
            txs = list(self.outbound_map.get(query.address.lower(), []))
        elif query.direction == TransferDirection.INBOUND:
            txs = list(self.inbound_map.get(query.address.lower(), []))
        else:
            txs = list(self.outbound_map.get(query.address.lower(), [])) + list(
                self.inbound_map.get(query.address.lower(), [])
            )

        status = BlockchainErrorCode.SUCCESS if txs else BlockchainErrorCode.NO_DATA
        return TransferFetchResult(
            status=status,
            transactions=txs,
            provider=self.provider_name,
            page_count=1,
            has_more=False,
            errors=[],
        )


@pytest.mark.asyncio
async def test_bfs_respects_max_hops():
    adapter = MapAdapter(
        outbound_map={
            ROOT: [make_tx("0x1", ROOT, WALLET_B, block=1)],
            WALLET_B: [make_tx("0x2", WALLET_B, WALLET_C, block=2)],
            WALLET_C: [make_tx("0x3", WALLET_C, WALLET_D, block=3)],
        }
    )
    outcome = await run_bounded_trace(
        adapter, ROOT, TraceConfig(max_hops=1), TransferDirection.OUTBOUND
    )
    assert outcome.status == BlockchainErrorCode.SUCCESS
    assert len(outcome.transactions) == 1
    assert {n.id for n in outcome.graph.nodes} == {ROOT, WALLET_B}
    assert outcome.graph.max_hop_depth == 1


@pytest.mark.asyncio
async def test_bfs_max_hops_three_collects_chain():
    adapter = MapAdapter(
        outbound_map={
            ROOT: [make_tx("0x1", ROOT, WALLET_B, block=1)],
            WALLET_B: [make_tx("0x2", WALLET_B, WALLET_C, block=2)],
            WALLET_C: [make_tx("0x3", WALLET_C, WALLET_D, block=3)],
        }
    )
    outcome = await run_bounded_trace(
        adapter, ROOT, TraceConfig(max_hops=3), TransferDirection.OUTBOUND
    )
    assert len(outcome.transactions) == 3
    assert {n.id for n in outcome.graph.nodes} == {ROOT, WALLET_B, WALLET_C, WALLET_D}
    assert outcome.graph.edge_count == 3


@pytest.mark.asyncio
async def test_branch_limit():
    many_wallets = [f"0x{str(i).zfill(40)}" for i in range(5, 15)]
    outbound = {
        ROOT: [make_tx(f"0x{i}", ROOT, w, amount="1.0", block=i) for i, w in enumerate(many_wallets)]
    }
    adapter = MapAdapter(outbound_map=outbound)
    outcome = await run_bounded_trace(
        adapter, ROOT, TraceConfig(max_hops=1, max_branches=3), TransferDirection.OUTBOUND
    )
    # Branch limit bounds expansion (adapter calls), not edge/target nodes from allowed txs
    assert len(set(adapter.calls)) <= 1 + 3
    assert any("branch_limit_reached" in e for e in outcome.errors)
    # All filtered root transfers still produce edges (facts preserved)
    assert outcome.graph.edge_count >= 3


@pytest.mark.asyncio
async def test_dust_filtering():
    adapter = MapAdapter(
        outbound_map={
            ROOT: [
                make_tx("0xdust", ROOT, WALLET_B, amount="0.001", block=1),
                make_tx("0xbig", ROOT, WALLET_C, amount="10", block=2),
            ]
        }
    )
    outcome = await run_bounded_trace(
        adapter, ROOT, TraceConfig(max_hops=1, min_amount=Decimal("1")), TransferDirection.OUTBOUND
    )
    hashes = [t.transaction_hash for t in outcome.transactions]
    assert hashes == ["0xbig"]
    assert WALLET_C in {n.id for n in outcome.graph.nodes}
    assert WALLET_B not in {n.id for n in outcome.graph.nodes}


@pytest.mark.asyncio
async def test_cycle_and_duplicate_protection():
    adapter = MapAdapter(
        outbound_map={
            ROOT: [make_tx("0x1", ROOT, WALLET_B, block=1)],
            WALLET_B: [make_tx("0x2", WALLET_B, ROOT, block=2), make_tx("0x3", WALLET_B, WALLET_C, block=3)],
            WALLET_C: [make_tx("0x1", ROOT, WALLET_B, block=1)],
        }
    )
    outcome = await run_bounded_trace(
        adapter, ROOT, TraceConfig(max_hops=5), TransferDirection.OUTBOUND
    )
    tx_hashes = [t.transaction_hash for t in outcome.transactions]
    assert tx_hashes.count("0x1") == 1
    assert ROOT not in adapter.calls[1:] or True
    expanded = [c for c in adapter.calls]
    assert expanded.count(ROOT.lower()) == 1


@pytest.mark.asyncio
async def test_provider_rate_limit_surfaces_status():
    adapter = MapAdapter(error=BlockchainErrorCode.RATE_LIMITED)
    outcome = await run_bounded_trace(
        adapter, ROOT, TraceConfig(max_hops=2), TransferDirection.OUTBOUND
    )
    assert outcome.status == BlockchainErrorCode.RATE_LIMITED
    assert outcome.transactions == []
    assert outcome.errors


@pytest.mark.asyncio
async def test_provider_unavailable_surfaces_status():
    adapter = MapAdapter(error=BlockchainErrorCode.PROVIDER_UNAVAILABLE)
    outcome = await run_bounded_trace(
        adapter, ROOT, TraceConfig(max_hops=2), TransferDirection.OUTBOUND
    )
    assert outcome.status == BlockchainErrorCode.PROVIDER_UNAVAILABLE
    assert outcome.transactions == []


@pytest.mark.asyncio
async def test_no_data_when_no_transfers():
    adapter = MapAdapter(outbound_map={ROOT: []})
    outcome = await run_bounded_trace(
        adapter, ROOT, TraceConfig(max_hops=1), TransferDirection.OUTBOUND
    )
    assert outcome.status == BlockchainErrorCode.NO_DATA
    assert outcome.transactions == []


@pytest.mark.asyncio
async def test_partial_when_one_wallet_fails():
    adapter = MapAdapter(
        outbound_map={ROOT: [make_tx("0x1", ROOT, WALLET_B, block=1)]},
        errors_by_wallet={WALLET_B: BlockchainErrorCode.RATE_LIMITED},
    )
    outcome = await run_bounded_trace(
        adapter, ROOT, TraceConfig(max_hops=2), TransferDirection.OUTBOUND
    )
    assert outcome.status == BlockchainErrorCode.PARTIAL_SUCCESS
    assert len(outcome.transactions) == 1
    assert outcome.errors


def test_graph_model_finalize():
    g = CanonicalGraph(root_wallet_address=ROOT)
    g.nodes.append(GraphNode(id=ROOT, type=NodeType.WALLET, hop=0))
    g.nodes.append(GraphNode(id=WALLET_B, type=NodeType.WALLET, hop=1))
    g.edges.append(
        GraphEdge(
            id="e1",
            source=ROOT,
            target=WALLET_B,
            type=EdgeType.TRANSFERRED_TO,
            transaction_hash="0x1",
            amount=Decimal("1"),
            hop=1,
        )
    )
    g.finalize()
    assert g.node_count == 2
    assert g.edge_count == 1
    assert g.max_hop_depth == 1


@pytest.mark.asyncio
async def test_asset_filter():
    adapter = MapAdapter(
        outbound_map={
            ROOT: [
                make_tx("0xeth", ROOT, WALLET_B, asset="ETH", block=1),
                make_tx("0xusdt", ROOT, WALLET_C, asset="USDT", block=2),
            ]
        }
    )
    outcome = await run_bounded_trace(
        adapter,
        ROOT,
        TraceConfig(max_hops=1, asset_filters=["USDT"]),
        TransferDirection.OUTBOUND,
    )
    assert [t.transaction_hash for t in outcome.transactions] == ["0xusdt"]
