import logging
from collections import deque
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple

from app.services.blockchain import (
    BlockchainAdapter,
    BlockchainErrorCode,
    CanonicalTransaction,
    TransferDirection,
    TransferFetchResult,
    TransferQuery,
)
from app.services.graph.model import (
    CanonicalGraph,
    EdgeType,
    GraphEdge,
    GraphNode,
    NodeType,
    TraceConfig,
)

logger = logging.getLogger("ledgerlens.tracing")

_TERMINAL_STATUSES = {
    BlockchainErrorCode.RATE_LIMITED,
    BlockchainErrorCode.PROVIDER_UNAVAILABLE,
    BlockchainErrorCode.INVALID_INPUT,
    BlockchainErrorCode.FAILED,
}


class TraceOutcome:
    def __init__(
        self,
        status: BlockchainErrorCode,
        transactions: List[CanonicalTransaction],
        graph: CanonicalGraph,
        errors: List[str],
        provider: str,
        pages_fetched: int = 0,
    ) -> None:
        self.status = status
        self.transactions = transactions
        self.graph = graph
        self.errors = errors
        self.provider = provider
        self.pages_fetched = pages_fetched

    @property
    def summary(self) -> dict:
        assets: Dict[str, Decimal] = {}
        for tx in self.transactions:
            key = tx.asset or "UNKNOWN"
            assets[key] = assets.get(key, Decimal("0")) + tx.amount
        return {
            "wallet_count": sum(1 for n in self.graph.nodes if n.type == NodeType.WALLET),
            "transaction_count": len(self.transactions),
            "edge_count": self.graph.edge_count,
            "max_hop_depth": self.graph.max_hop_depth,
            "assets_transferred": {k: str(v) for k, v in sorted(assets.items())},
            "pages_fetched": self.pages_fetched,
            "provider": self.provider,
        }


def _sort_key(tx: CanonicalTransaction) -> Tuple:
    return (
        tx.block_number if tx.block_number is not None else -1,
        tx.transaction_hash,
        tx.provider_reference,
        tx.from_address,
        tx.to_address or "",
    )


def _passes_filters(
    tx: CanonicalTransaction,
    root: str,
    direction: TransferDirection,
    config: TraceConfig,
) -> bool:
    root_l = root.lower()
    if direction == TransferDirection.OUTBOUND:
        if (tx.from_address or "").lower() != root_l:
            return False
    elif direction == TransferDirection.INBOUND:
        if (tx.to_address or "").lower() != root_l:
            return False
    else:
        if (tx.from_address or "").lower() != root_l and (tx.to_address or "").lower() != root_l:
            return False

    if config.min_amount is not None and tx.amount < config.min_amount:
        return False

    if config.asset_filters:
        allowed = {a.strip().lower() for a in config.asset_filters}
        asset = (tx.asset or "").strip().lower()
        contract = (tx.token_contract or "").strip().lower()
        if asset not in allowed and contract not in allowed:
            return False

    if config.time_range_start and tx.block_timestamp and tx.block_timestamp < config.time_range_start:
        return False
    if config.time_range_end and tx.block_timestamp and tx.block_timestamp > config.time_range_end:
        return False

    if not tx.to_address:
        return False
    return True


def _counterparty(tx: CanonicalTransaction, wallet: str, direction: TransferDirection) -> Optional[str]:
    wallet_l = wallet.lower()
    if direction == TransferDirection.INBOUND:
        return tx.from_address
    if direction == TransferDirection.BOTH:
        if (tx.from_address or "").lower() == wallet_l:
            return tx.to_address
        return tx.from_address
    return tx.to_address


async def run_bounded_trace(
    adapter: BlockchainAdapter,
    start_wallet: str,
    config: TraceConfig,
    direction: TransferDirection = TransferDirection.OUTBOUND,
    chain: str = "ethereum",
) -> TraceOutcome:
    root = (start_wallet or "").strip().lower()
    graph = CanonicalGraph(root_wallet_address=root, blockchain=chain)
    errors: List[str] = []
    collected: Dict[str, CanonicalTransaction] = {}
    pages_fetched = 0
    terminal_hits: List[BlockchainErrorCode] = []
    soft_failures = False
    provider = adapter.provider_name

    graph.nodes.append(
        GraphNode(id=root, type=NodeType.WALLET, label="start_wallet", hop=0, metadata={"root": True})
    )

    visited: Set[str] = {root}
    frontier: deque[Tuple[str, int]] = deque([(root, 0)])
    edge_keys: Set[str] = set()

    while frontier:
        wallet, hop = frontier.popleft()
        if hop >= config.max_hops:
            continue

        query = TransferQuery(
            address=wallet,
            direction=direction,
            max_pages=config.max_pages_per_wallet,
            max_transfers=config.max_branches * 4,
            page_size=config.page_size,
        )
        try:
            result: TransferFetchResult = await adapter.fetch_transfers(query)
        except Exception as exc:  # noqa: BLE001 - adapter should not raise; surface explicitly
            errors.append(f"wallet={wallet} hop={hop} unexpected_adapter_error: {exc}")
            terminal_hits.append(BlockchainErrorCode.FAILED)
            continue

        pages_fetched += result.page_count
        for err in result.errors:
            errors.append(f"wallet={wallet} hop={hop}: {err}")

        if result.status in _TERMINAL_STATUSES:
            if result.status != BlockchainErrorCode.INVALID_INPUT or not result.transactions:
                terminal_hits.append(result.status)
            if not result.transactions:
                continue
            soft_failures = True
        if result.status == BlockchainErrorCode.PARTIAL_SUCCESS:
            soft_failures = True

        txs = [t for t in result.transactions if _passes_filters(t, wallet, direction, config)]
        txs.sort(key=_sort_key)

        branch_candidates: List[Tuple[str, CanonicalTransaction]] = []
        for tx in txs:
            key = (tx.transaction_hash, tx.from_address, tx.to_address or "", tx.provider_reference)
            tx_key = "|".join(key)
            is_new_tx = tx_key not in collected
            if is_new_tx:
                collected[tx_key] = tx
            next_hop = hop + 1
            cp = _counterparty(tx, wallet, direction)
            if cp:
                cp_l = cp.lower()
                edge_id = f"{tx.transaction_hash}:{wallet}:{cp_l}:{tx.provider_reference}"
                if edge_id not in edge_keys:
                    edge_keys.add(edge_id)
                    graph.edges.append(
                        GraphEdge(
                            id=edge_id,
                            source=wallet,
                            target=cp_l,
                            type=EdgeType.TRANSFERRED_TO,
                            transaction_hash=tx.transaction_hash,
                            amount=tx.amount,
                            asset=tx.asset,
                            timestamp=tx.block_timestamp,
                            hop=next_hop,
                        )
                    )
                    if cp_l not in {n.id for n in graph.nodes}:
                        graph.nodes.append(
                            GraphNode(id=cp_l, type=NodeType.WALLET, hop=next_hop, metadata={})
                        )
                branch_candidates.append((cp_l, tx))

        branch_candidates.sort(key=lambda item: (-item[1].amount, item[0], item[1].transaction_hash))
        expanded = 0
        for cp_l, _tx in branch_candidates:
            if cp_l in visited:
                continue
            if expanded >= config.max_branches:
                errors.append(
                    f"wallet={wallet} hop={hop}: branch_limit_reached max_branches={config.max_branches}"
                )
                break
            visited.add(cp_l)
            frontier.append((cp_l, hop + 1))
            expanded += 1

    transactions = sorted(collected.values(), key=_sort_key)
    graph.finalize()

    other_errors = [
        e for e in errors if "branch_limit_reached" not in e and "page_limit_reached" not in e
    ]

    if terminal_hits and transactions:
        status = BlockchainErrorCode.PARTIAL_SUCCESS
    elif terminal_hits and not transactions:
        status = terminal_hits[0]
    elif transactions and (soft_failures or other_errors):
        status = BlockchainErrorCode.PARTIAL_SUCCESS
    elif transactions:
        status = BlockchainErrorCode.SUCCESS
    elif other_errors:
        status = BlockchainErrorCode.FAILED
    else:
        status = BlockchainErrorCode.NO_DATA

    if not transactions and status == BlockchainErrorCode.SUCCESS:
        status = BlockchainErrorCode.NO_DATA

    return TraceOutcome(
        status=status,
        transactions=transactions,
        graph=graph,
        errors=list(dict.fromkeys(errors)),
        provider=provider,
        pages_fetched=pages_fetched,
    )


def graph_nodes_index(graph: CanonicalGraph) -> Set[str]:
    return {n.id for n in graph.nodes}
