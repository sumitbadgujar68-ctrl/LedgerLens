from collections import defaultdict
from decimal import Decimal
from typing import List, Optional

from app.services.graph.model import CanonicalGraph, GraphEdge, GraphNode
from app.services.patterns.models import PatternFinding, PatternType

RAPID_FORWARD_TIME_DELTA_SECONDS = 900
RAPID_FORWARD_RETAIN_THRESHOLD = Decimal("0.15")
PEEL_CHAIN_MIN_LENGTH = 3
PEEL_CHAIN_PASS_THROUGH_RATIO = Decimal("0.80")
FAN_OUT_MIN_RECIPIENTS = 5
FAN_OUT_TIME_WINDOW_SECONDS = 7200
FAN_IN_MIN_SENDERS = 5
FAN_IN_TIME_WINDOW_SECONDS = 7200
VOLUME_CONCENTRATION_THRESHOLD = Decimal("0.75")
REPEATED_COUNTERPARTY_MIN_APPEARANCES = 2


def _edges_by_source(graph: CanonicalGraph) -> dict:
    result = defaultdict(list)
    for e in graph.edges:
        result[e.source].append(e)
    return result


def _edges_by_target(graph: CanonicalGraph) -> dict:
    result = defaultdict(list)
    for e in graph.edges:
        result[e.target].append(e)
    return result


def _total_volume(edges: List[GraphEdge]) -> Decimal:
    return sum((e.amount for e in edges), Decimal("0"))


def detect_rapid_forwarding(graph: CanonicalGraph) -> List[PatternFinding]:
    findings: List[PatternFinding] = []
    if not graph.edges:
        return findings

    by_target = _edges_by_target(graph)
    by_source = _edges_by_source(graph)

    for node in graph.nodes:
        addr = node.id
        inbound = by_target.get(addr, [])
        outbound = by_source.get(addr, [])
        if not inbound or not outbound:
            continue

        timed_in = [e for e in inbound if e.timestamp is not None]
        timed_out = [e for e in outbound if e.timestamp is not None]
        if not timed_in or not timed_out:
            continue

        for in_edge in timed_in:
            for out_edge in timed_out:
                delta = (out_edge.timestamp - in_edge.timestamp).total_seconds()
                if delta < 0 or delta > RAPID_FORWARD_TIME_DELTA_SECONDS:
                    continue
                if in_edge.amount == 0:
                    continue
                retained = (in_edge.amount - out_edge.amount) / in_edge.amount
                if retained <= RAPID_FORWARD_RETAIN_THRESHOLD:
                    findings.append(
                        PatternFinding(
                            pattern_type=PatternType.RAPID_FORWARDING,
                            wallet_address=addr,
                            confidence=Decimal("1.00"),
                            description=(
                                f"Forwarded {(1 - retained) * 100:.1f}% of incoming volume "
                                f"within {int(delta)}s"
                            ),
                            evidence={
                                "inbound_tx": in_edge.transaction_hash,
                                "outbound_tx": out_edge.transaction_hash,
                                "time_delta_seconds": int(delta),
                                "inbound_amount": str(in_edge.amount),
                                "outbound_amount": str(out_edge.amount),
                                "retained_ratio": str(round(retained, 4)),
                            },
                            metrics={
                                "time_delta_seconds": int(delta),
                                "forward_ratio": str(round(1 - retained, 4)),
                            },
                        )
                    )
    return findings


def detect_peel_chain(graph: CanonicalGraph) -> List[PatternFinding]:
    findings: List[PatternFinding] = []
    if not graph.nodes or not graph.edges:
        return findings

    by_source = _edges_by_source(graph)
    by_target = _edges_by_target(graph)

    visited_chains: set = set()
    for node in graph.nodes:
        addr = node.id
        ins = by_target.get(addr, [])
        outs = by_source.get(addr, [])
        # Must have exactly one input and exactly two outputs to be a single-input/two-output transfer
        if len(ins) == 1 and len(outs) == 2:
            # Check the pass-through ratio: larger output >= PEEL_CHAIN_PASS_THROUGH_RATIO of total output
            amounts = sorted([e.amount for e in outs], reverse=True)
            if amounts[0] == 0:
                continue
            pass_ratio = amounts[0] / (amounts[0] + amounts[1])
            if pass_ratio < PEEL_CHAIN_PASS_THROUGH_RATIO:
                continue

            # Follow the chain forward via the larger output each time
            chain = [addr]
            current = addr
            while True:
                current_outs = by_source.get(current, [])
                if len(current_outs) != 2:
                    break
                amounts = sorted([e.amount for e in current_outs], reverse=True)
                if amounts[0] == 0:
                    break
                pass_ratio = amounts[0] / (amounts[0] + amounts[1])
                if pass_ratio < PEEL_CHAIN_PASS_THROUGH_RATIO:
                    break
                next_node = max(current_outs, key=lambda e: e.amount).target
                if next_node in chain:  # avoid cycles
                    break
                chain.append(next_node)
                current = next_node

            if len(chain) >= PEEL_CHAIN_MIN_LENGTH:
                key = tuple(chain)
                if key not in visited_chains:
                    visited_chains.add(key)
                    # Collect all edges in the chain (for evidence)
                    all_edges: List[GraphEdge] = []
                    for addr in chain:
                        all_edges.extend(by_source.get(addr, []))
                    findings.append(
                        PatternFinding(
                            pattern_type=PatternType.PEEL_CHAIN,
                            wallet_address=chain[0],
                            confidence=Decimal("1.00"),
                            description=(
                                f"Peel chain of length {len(chain)} detected starting at {chain[0]}"
                            ),
                            evidence={
                                "chain": chain,
                                "chain_length": len(chain),
                                "tx_hashes": [e.transaction_hash for e in all_edges],
                            },
                            metrics={
                                "chain_length": len(chain),
                                "total_volume": str(_total_volume(all_edges)),
                            },
                        )
                    )
    return findings


def detect_high_fan_out(graph: CanonicalGraph) -> List[PatternFinding]:
    findings: List[PatternFinding] = []
    if not graph.edges:
        return findings

    by_source = _edges_by_source(graph)

    for node in graph.nodes:
        addr = node.id
        outs = by_source.get(addr, [])
        timed = [e for e in outs if e.timestamp is not None]

        if len(outs) >= FAN_OUT_MIN_RECIPIENTS and not timed:
            recipients = list({e.target for e in outs})
            if len(recipients) >= FAN_OUT_MIN_RECIPIENTS:
                findings.append(
                    PatternFinding(
                        pattern_type=PatternType.HIGH_FAN_OUT,
                        wallet_address=addr,
                        confidence=Decimal("1.00"),
                        description=(
                            f"Distributed funds to {len(recipients)} distinct recipients"
                        ),
                        evidence={
                            "recipient_addresses": recipients,
                            "tx_hashes": [e.transaction_hash for e in outs],
                        },
                        metrics={
                            "recipient_count": len(recipients),
                            "total_volume": str(_total_volume(outs)),
                        },
                    )
                )
            continue

        if len(timed) < FAN_OUT_MIN_RECIPIENTS:
            continue

        min_ts = min(e.timestamp for e in timed)
        max_ts = max(e.timestamp for e in timed)
        window = (max_ts - min_ts).total_seconds()
        if window <= FAN_OUT_TIME_WINDOW_SECONDS:
            recipients = list({e.target for e in timed})
            if len(recipients) >= FAN_OUT_MIN_RECIPIENTS:
                findings.append(
                    PatternFinding(
                        pattern_type=PatternType.HIGH_FAN_OUT,
                        wallet_address=addr,
                        confidence=Decimal("1.00"),
                        description=(
                            f"Distributed funds to {len(recipients)} distinct recipients "
                            f"within {int(window)}s"
                        ),
                        evidence={
                            "recipient_addresses": recipients,
                            "tx_hashes": [e.transaction_hash for e in timed],
                            "window_seconds": int(window),
                        },
                        metrics={
                            "recipient_count": len(recipients),
                            "window_seconds": int(window),
                            "total_volume": str(_total_volume(timed)),
                        },
                    )
                )
    return findings


def detect_high_fan_in(graph: CanonicalGraph) -> List[PatternFinding]:
    findings: List[PatternFinding] = []
    if not graph.edges:
        return findings

    by_target = _edges_by_target(graph)

    for node in graph.nodes:
        addr = node.id
        ins = by_target.get(addr, [])
        timed = [e for e in ins if e.timestamp is not None]

        if len(ins) >= FAN_IN_MIN_SENDERS and not timed:
            senders = list({e.source for e in ins})
            if len(senders) >= FAN_IN_MIN_SENDERS:
                findings.append(
                    PatternFinding(
                        pattern_type=PatternType.HIGH_FAN_IN,
                        wallet_address=addr,
                        confidence=Decimal("1.00"),
                        description=(
                            f"Received funds from {len(senders)} distinct senders"
                        ),
                        evidence={
                            "sender_addresses": senders,
                            "tx_hashes": [e.transaction_hash for e in ins],
                        },
                        metrics={
                            "sender_count": len(senders),
                            "total_volume": str(_total_volume(ins)),
                        },
                    )
                )
            continue

        if len(timed) < FAN_IN_MIN_SENDERS:
            continue

        min_ts = min(e.timestamp for e in timed)
        max_ts = max(e.timestamp for e in timed)
        window = (max_ts - min_ts).total_seconds()
        if window <= FAN_IN_TIME_WINDOW_SECONDS:
            senders = list({e.source for e in timed})
            if len(senders) >= FAN_IN_MIN_SENDERS:
                findings.append(
                    PatternFinding(
                        pattern_type=PatternType.HIGH_FAN_IN,
                        wallet_address=addr,
                        confidence=Decimal("1.00"),
                        description=(
                            f"Received funds from {len(senders)} distinct senders "
                            f"within {int(window)}s"
                        ),
                        evidence={
                            "sender_addresses": senders,
                            "tx_hashes": [e.transaction_hash for e in timed],
                            "window_seconds": int(window),
                        },
                        metrics={
                            "sender_count": len(senders),
                            "window_seconds": int(window),
                            "total_volume": str(_total_volume(timed)),
                        },
                    )
                )
    return findings


def detect_cyclic_flow(graph: CanonicalGraph) -> List[PatternFinding]:
    findings: List[PatternFinding] = []
    if not graph.edges:
        return findings

    adj: dict = defaultdict(set)
    edge_map: dict = defaultdict(list)
    for e in graph.edges:
        adj[e.source].add(e.target)
        edge_map[(e.source, e.target)].append(e)

    visited_cycles: set = set()

    def _dfs(start: str, current: str, path: List[str], path_set: set):
        for neighbor in adj.get(current, []):
            if neighbor == start and len(path) >= 2:
                cycle_key = tuple(sorted(path))
                if cycle_key not in visited_cycles:
                    visited_cycles.add(cycle_key)
                    tx_hashes = []
                    cycle_with_start = path + [start]
                    for i in range(len(cycle_with_start) - 1):
                        edges = edge_map.get((cycle_with_start[i], cycle_with_start[i + 1]), [])
                        tx_hashes.extend(e.transaction_hash for e in edges)
                    findings.append(
                        PatternFinding(
                            pattern_type=PatternType.CYCLIC_FLOW,
                            wallet_address=start,
                            confidence=Decimal("1.00"),
                            description=(
                                f"Cyclic fund flow detected: {' → '.join(cycle_with_start)}"
                            ),
                            evidence={
                                "cycle_path": cycle_with_start,
                                "tx_hashes": tx_hashes,
                            },
                            metrics={"cycle_length": len(path)},
                        )
                    )
            elif neighbor not in path_set:
                path_set.add(neighbor)
                _dfs(start, neighbor, path + [neighbor], path_set)
                path_set.discard(neighbor)

    all_nodes = {n.id for n in graph.nodes}
    for node_id in all_nodes:
        _dfs(node_id, node_id, [node_id], {node_id})
    return findings


def detect_repeated_counterparties(graph: CanonicalGraph) -> List[PatternFinding]:
    findings: List[PatternFinding] = []
    if not graph.edges:
        return findings

    counterparty_nodes: dict = defaultdict(set)
    for edge in graph.edges:
        counterparty_nodes[edge.target].add(edge.source)
        counterparty_nodes[edge.source].add(edge.target)

    node_hops: dict = {n.id: n.hop for n in graph.nodes}

    address_counterparty_hops: dict = defaultdict(set)
    for addr, counterparties in counterparty_nodes.items():
        for cp in counterparties:
            cp_hop = node_hops.get(cp, 0)
            address_counterparty_hops[addr].add(cp_hop)

    reported: set = set()
    for addr, hops in address_counterparty_hops.items():
        in_edges = [e for e in graph.edges if e.target == addr]
        out_edges = [e for e in graph.edges if e.source == addr]
        # Require at least two incoming OR two outgoing edges (to avoid linear chain false positives)
        if (len(in_edges) >= 2 or len(out_edges) >= 2) and addr not in reported:
            appearances = sorted(hops)
            reported.add(addr)
            findings.append(
                PatternFinding(
                    pattern_type=PatternType.REPEATED_COUNTERPARTIES,
                    wallet_address=addr,
                    confidence=Decimal("1.00"),
                    description=(
                        f"Address appears across {len(hops)} distinct hops in trace"
                    ),
                    evidence={
                        "hop_appearances": appearances,
                        "inbound_tx_hashes": [e.transaction_hash for e in in_edges],
                        "outbound_tx_hashes": [e.transaction_hash for e in out_edges],
                    },
                    metrics={
                        "hop_count": len(hops),
                        "total_interactions": len(in_edges) + len(out_edges),
                    },
                )
            )
    return findings


def detect_volume_concentration(graph: CanonicalGraph) -> List[PatternFinding]:
    findings: List[PatternFinding] = []
    if not graph.edges:
        return findings

    by_target = _edges_by_target(graph)
    total_vol = _total_volume(graph.edges)
    if total_vol == 0:
        return findings

    for node in graph.nodes:
        addr = node.id
        inbound = by_target.get(addr, [])
        if not inbound:
            continue
        node_vol = _total_volume(inbound)
        ratio = node_vol / total_vol
        if ratio >= VOLUME_CONCENTRATION_THRESHOLD:
            findings.append(
                PatternFinding(
                    pattern_type=PatternType.VOLUME_CONCENTRATION,
                    wallet_address=addr,
                    confidence=Decimal("1.00"),
                    description=(
                        f"Address received {ratio * 100:.1f}% of total traced volume"
                    ),
                    evidence={
                        "node_volume": str(node_vol),
                        "total_volume": str(total_vol),
                        "concentration_ratio": str(round(ratio, 4)),
                        "tx_hashes": [e.transaction_hash for e in inbound],
                    },
                    metrics={
                        "concentration_ratio": str(round(ratio, 4)),
                        "node_volume": str(node_vol),
                        "total_volume": str(total_vol),
                    },
                )
            )
    return findings
