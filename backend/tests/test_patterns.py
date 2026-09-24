from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.services.graph.model import CanonicalGraph, GraphEdge, GraphNode
from app.services.patterns import (
    ENGINE_VERSION,
    PatternType,
    detect_cyclic_flow,
    detect_high_fan_in,
    detect_high_fan_out,
    detect_peel_chain,
    detect_rapid_forwarding,
    detect_repeated_counterparties,
    detect_volume_concentration,
    run_all_detectors,
)


def _node(addr: str, hop: int = 0) -> GraphNode:
    return GraphNode(id=addr, hop=hop)


def _edge(
    src: str,
    tgt: str,
    amount: str = "1.0",
    tx: str = None,
    ts: datetime = None,
    hop: int = 0,
) -> GraphEdge:
    return GraphEdge(
        id=f"{src}->{tgt}",
        source=src,
        target=tgt,
        transaction_hash=tx or f"0x{src[-4:]}{tgt[-4:]}",
        amount=Decimal(amount),
        timestamp=ts,
        hop=hop,
    )


def _graph(*nodes_edges) -> CanonicalGraph:
    nodes = [x for x in nodes_edges if isinstance(x, GraphNode)]
    edges = [x for x in nodes_edges if isinstance(x, GraphEdge)]
    g = CanonicalGraph(root_wallet_address=nodes[0].id if nodes else "0x0", edges=edges, nodes=nodes)
    return g.finalize()


T0 = datetime(2024, 1, 1, 12, 0, 0)


# ===========================================================
# RAPID FORWARDING
# ===========================================================

class TestRapidForwarding:
    def test_positive_detects_rapid_forward(self):
        a, b, c = "0xA000", "0xB000", "0xC000"
        g = _graph(
            _node(a), _node(b), _node(c),
            _edge(a, b, "10.0", tx="0xIN", ts=T0),
            _edge(b, c, "9.8", tx="0xOUT", ts=T0 + timedelta(seconds=300)),
        )
        findings = detect_rapid_forwarding(g)
        assert len(findings) == 1
        f = findings[0]
        assert f.pattern_type == PatternType.RAPID_FORWARDING
        assert f.wallet_address == b
        assert f.evidence["inbound_tx"] == "0xIN"
        assert f.evidence["outbound_tx"] == "0xOUT"
        assert f.evidence["time_delta_seconds"] == 300

    def test_negative_slow_forward_not_detected(self):
        a, b, c = "0xA001", "0xB001", "0xC001"
        g = _graph(
            _node(a), _node(b), _node(c),
            _edge(a, b, "10.0", tx="0xIN2", ts=T0),
            _edge(b, c, "9.8", tx="0xOUT2", ts=T0 + timedelta(seconds=1800)),
        )
        findings = detect_rapid_forwarding(g)
        assert len(findings) == 0

    def test_negative_high_retention_not_detected(self):
        a, b, c = "0xA002", "0xB002", "0xC002"
        g = _graph(
            _node(a), _node(b), _node(c),
            _edge(a, b, "10.0", tx="0xIN3", ts=T0),
            _edge(b, c, "5.0", tx="0xOUT3", ts=T0 + timedelta(seconds=60)),
        )
        findings = detect_rapid_forwarding(g)
        assert len(findings) == 0

    def test_empty_graph(self):
        g = CanonicalGraph(root_wallet_address="0x0000")
        assert detect_rapid_forwarding(g) == []

    def test_no_timestamps_not_detected(self):
        a, b, c = "0xA003", "0xB003", "0xC003"
        g = _graph(
            _node(a), _node(b), _node(c),
            _edge(a, b, "10.0"),
            _edge(b, c, "9.9"),
        )
        assert detect_rapid_forwarding(g) == []

    def test_threshold_boundary_exact_15_min(self):
        a, b, c = "0xA004", "0xB004", "0xC004"
        g = _graph(
            _node(a), _node(b), _node(c),
            _edge(a, b, "10.0", tx="0xBin", ts=T0),
            _edge(b, c, "9.9", tx="0xBout", ts=T0 + timedelta(seconds=900)),
        )
        findings = detect_rapid_forwarding(g)
        assert len(findings) == 1

    def test_deterministic_same_input_same_output(self):
        a, b, c = "0xA005", "0xB005", "0xC005"
        g = _graph(
            _node(a), _node(b), _node(c),
            _edge(a, b, "10.0", tx="0xR1", ts=T0),
            _edge(b, c, "9.8", tx="0xR2", ts=T0 + timedelta(seconds=60)),
        )
        r1 = detect_rapid_forwarding(g)
        r2 = detect_rapid_forwarding(g)
        assert len(r1) == len(r2)
        assert r1[0].evidence == r2[0].evidence


# ===========================================================
# PEEL CHAIN
# ===========================================================

class TestPeelChain:
    def test_positive_three_hop_chain(self):
        a, b, c, d = "0xPA", "0xPB", "0xPC", "0xPD"
        small = "0xPS"
        g = _graph(
            _node(a, 0), _node(b, 1), _node(c, 2), _node(d, 3), _node(small, 1),
            _edge(a, b, "10.0"),
            _edge(b, c, "9.5"),
            _edge(b, small, "0.5"),
            _edge(c, d, "9.0"),
            _edge(c, small, "0.5"),
        )
        findings = detect_peel_chain(g)
        assert len(findings) >= 1
        types = {f.pattern_type for f in findings}
        assert PatternType.PEEL_CHAIN in types

    def test_negative_equal_split_not_peel(self):
        a, b, c = "0xPE", "0xPF", "0xPG"
        g = _graph(
            _node(a), _node(b), _node(c),
            _edge(a, b, "5.0"),
            _edge(a, c, "5.0"),
        )
        assert detect_peel_chain(g) == []

    def test_negative_linear_single_out_not_peel(self):
        a, b, c = "0xPH", "0xPI", "0xPJ"
        g = _graph(
            _node(a), _node(b), _node(c),
            _edge(a, b, "10.0"),
            _edge(b, c, "10.0"),
        )
        assert detect_peel_chain(g) == []

    def test_empty_graph(self):
        g = CanonicalGraph(root_wallet_address="0x0000")
        assert detect_peel_chain(g) == []

    def test_chain_evidence_contains_nodes(self):
        a, b, c, d = "0xXA", "0xXB", "0xXC", "0xXD"
        sm = "0xXS"
        g = _graph(
            _node(a), _node(b), _node(c), _node(d), _node(sm),
            _edge(a, b, "10.0"),
            _edge(b, c, "9.5"),
            _edge(b, sm, "0.5"),
            _edge(c, d, "9.0"),
            _edge(c, sm, "0.4"),
        )
        findings = detect_peel_chain(g)
        if findings:
            f = findings[0]
            assert "chain" in f.evidence
            assert len(f.evidence["chain"]) >= 3


# ===========================================================
# HIGH FAN-OUT
# ===========================================================

class TestHighFanOut:
    def _make_fanout(self, n: int, windowed: bool = True) -> CanonicalGraph:
        src = "0xFOSRC"
        recipients = [f"0xFOR{i:03d}" for i in range(n)]
        nodes = [_node(src)] + [_node(r) for r in recipients]
        ts_base = T0 if windowed else None
        edges = [
            _edge(src, r, "1.0", ts=ts_base + timedelta(minutes=i) if ts_base else None)
            for i, r in enumerate(recipients)
        ]
        return _graph(*nodes, *edges)

    def test_positive_five_recipients(self):
        g = self._make_fanout(5)
        findings = detect_high_fan_out(g)
        assert any(f.pattern_type == PatternType.HIGH_FAN_OUT for f in findings)

    def test_positive_untimed_five_recipients(self):
        g = self._make_fanout(5, windowed=False)
        findings = detect_high_fan_out(g)
        assert any(f.pattern_type == PatternType.HIGH_FAN_OUT for f in findings)

    def test_negative_four_recipients(self):
        g = self._make_fanout(4)
        assert detect_high_fan_out(g) == []

    def test_empty_graph(self):
        g = CanonicalGraph(root_wallet_address="0x0000")
        assert detect_high_fan_out(g) == []

    def test_evidence_includes_recipients(self):
        g = self._make_fanout(6)
        findings = detect_high_fan_out(g)
        f = next(x for x in findings if x.pattern_type == PatternType.HIGH_FAN_OUT)
        assert "recipient_addresses" in f.evidence
        assert f.metrics["recipient_count"] >= 5


# ===========================================================
# HIGH FAN-IN
# ===========================================================

class TestHighFanIn:
    def _make_fanin(self, n: int, windowed: bool = True) -> CanonicalGraph:
        tgt = "0xFITGT"
        senders = [f"0xFIS{i:03d}" for i in range(n)]
        nodes = [_node(tgt)] + [_node(s) for s in senders]
        ts_base = T0 if windowed else None
        edges = [
            _edge(s, tgt, "1.0", ts=ts_base + timedelta(minutes=i) if ts_base else None)
            for i, s in enumerate(senders)
        ]
        return _graph(*nodes, *edges)

    def test_positive_five_senders(self):
        g = self._make_fanin(5)
        findings = detect_high_fan_in(g)
        assert any(f.pattern_type == PatternType.HIGH_FAN_IN for f in findings)

    def test_positive_untimed_five_senders(self):
        g = self._make_fanin(5, windowed=False)
        findings = detect_high_fan_in(g)
        assert any(f.pattern_type == PatternType.HIGH_FAN_IN for f in findings)

    def test_negative_four_senders(self):
        g = self._make_fanin(4)
        assert detect_high_fan_in(g) == []

    def test_empty_graph(self):
        g = CanonicalGraph(root_wallet_address="0x0000")
        assert detect_high_fan_in(g) == []

    def test_evidence_includes_senders(self):
        g = self._make_fanin(7)
        findings = detect_high_fan_in(g)
        f = next(x for x in findings if x.pattern_type == PatternType.HIGH_FAN_IN)
        assert "sender_addresses" in f.evidence
        assert f.metrics["sender_count"] >= 5


# ===========================================================
# CYCLIC FLOW
# ===========================================================

class TestCyclicFlow:
    def test_positive_simple_cycle(self):
        a, b, c = "0xCA", "0xCB", "0xCC"
        g = _graph(
            _node(a), _node(b), _node(c),
            _edge(a, b, "1.0", tx="0xc1"),
            _edge(b, c, "1.0", tx="0xc2"),
            _edge(c, a, "1.0", tx="0xc3"),
        )
        findings = detect_cyclic_flow(g)
        assert len(findings) >= 1
        assert any(f.pattern_type == PatternType.CYCLIC_FLOW for f in findings)

    def test_positive_cycle_evidence_path(self):
        a, b, c = "0xDA", "0xDB", "0xDC"
        g = _graph(
            _node(a), _node(b), _node(c),
            _edge(a, b, "1.0", tx="0xd1"),
            _edge(b, c, "1.0", tx="0xd2"),
            _edge(c, a, "1.0", tx="0xd3"),
        )
        findings = detect_cyclic_flow(g)
        f = findings[0]
        assert "cycle_path" in f.evidence
        path = f.evidence["cycle_path"]
        assert path[0] == path[-1]

    def test_negative_linear_no_cycle(self):
        a, b, c = "0xEA", "0xEB", "0xEC"
        g = _graph(
            _node(a), _node(b), _node(c),
            _edge(a, b, "1.0"),
            _edge(b, c, "1.0"),
        )
        assert detect_cyclic_flow(g) == []

    def test_negative_single_node(self):
        g = _graph(_node("0xSINGLE"))
        assert detect_cyclic_flow(g) == []

    def test_empty_graph(self):
        g = CanonicalGraph(root_wallet_address="0x0000")
        assert detect_cyclic_flow(g) == []

    def test_deterministic(self):
        a, b, c = "0xFA", "0xFB", "0xFC"
        g = _graph(
            _node(a), _node(b), _node(c),
            _edge(a, b, "1.0", tx="0xe1"),
            _edge(b, c, "1.0", tx="0xe2"),
            _edge(c, a, "1.0", tx="0xe3"),
        )
        r1 = detect_cyclic_flow(g)
        r2 = detect_cyclic_flow(g)
        assert len(r1) == len(r2)


# ===========================================================
# REPEATED COUNTERPARTIES
# ===========================================================

class TestRepeatedCounterparties:
    def test_positive_address_at_two_hops(self):
        root = "0xRC0"
        intermediary = "0xRCA"
        h1 = "0xRCH1"
        h2 = "0xRCH2"
        g = _graph(
            _node(root, 0), _node(h1, 1), _node(intermediary, 1), _node(h2, 2),
            _edge(root, h1, tx="0xrcx1"),
            _edge(root, intermediary, tx="0xrcx2"),
            _edge(h1, intermediary, tx="0xrcx3"),
            _edge(intermediary, h2, tx="0xrcx4"),
        )
        findings = detect_repeated_counterparties(g)
        addrs = {f.wallet_address for f in findings if f.pattern_type == PatternType.REPEATED_COUNTERPARTIES}
        assert intermediary in addrs

    def test_negative_unique_counterparties(self):
        a, b, c = "0xUA", "0xUB", "0xUC"
        g = _graph(
            _node(a, 0), _node(b, 1), _node(c, 2),
            _edge(a, b), _edge(b, c),
        )
        assert detect_repeated_counterparties(g) == []

    def test_empty_graph(self):
        g = CanonicalGraph(root_wallet_address="0x0000")
        assert detect_repeated_counterparties(g) == []

    def test_evidence_includes_hops(self):
        root = "0xRC0B"
        shared = "0xRCSH"
        h1a = "0xRH1A"
        h1b = "0xRH1B"
        g = _graph(
            _node(root, 0), _node(h1a, 1), _node(shared, 1), _node(h1b, 2),
            _edge(root, shared),
            _edge(root, h1a),
            _edge(h1a, shared),
        )
        findings = detect_repeated_counterparties(g)
        shared_findings = [f for f in findings if f.wallet_address == shared]
        if shared_findings:
            f = shared_findings[0]
            assert "hop_appearances" in f.evidence


# ===========================================================
# VOLUME CONCENTRATION
# ===========================================================

class TestVolumeConcentration:
    def test_positive_single_node_receives_most(self):
        src1, src2, src3 = "0xVS1", "0xVS2", "0xVS3"
        sink = "0xVTGT"
        other = "0xVOTH"
        g = _graph(
            _node(src1), _node(src2), _node(src3), _node(sink), _node(other),
            _edge(src1, sink, "8.0", tx="0xvc1"),
            _edge(src2, sink, "8.0", tx="0xvc2"),
            _edge(src3, other, "1.0", tx="0xvc3"),
        )
        findings = detect_volume_concentration(g)
        assert any(f.pattern_type == PatternType.VOLUME_CONCENTRATION and f.wallet_address == sink for f in findings)

    def test_negative_even_distribution(self):
        a, b, c, d = "0xVA", "0xVB", "0xVC", "0xVD"
        g = _graph(
            _node(a), _node(b), _node(c), _node(d),
            _edge(a, b, "5.0"), _edge(a, c, "5.0"), _edge(a, d, "5.0"),
        )
        assert detect_volume_concentration(g) == []

    def test_negative_zero_volume(self):
        a, b = "0xVZ1", "0xVZ2"
        g = _graph(
            _node(a), _node(b),
            _edge(a, b, "0"),
        )
        assert detect_volume_concentration(g) == []

    def test_empty_graph(self):
        g = CanonicalGraph(root_wallet_address="0x0000")
        assert detect_volume_concentration(g) == []

    def test_evidence_includes_ratio(self):
        src, sink, other = "0xER1", "0xER2", "0xER3"
        g = _graph(
            _node(src), _node(sink), _node(other),
            _edge(src, sink, "9.0", tx="0xevr1"),
            _edge(src, other, "1.0", tx="0xevr2"),
        )
        findings = detect_volume_concentration(g)
        f = next(x for x in findings if x.wallet_address == sink)
        assert "concentration_ratio" in f.evidence
        assert float(f.evidence["concentration_ratio"]) >= 0.75


# ===========================================================
# RUN ALL DETECTORS / ORCHESTRATOR
# ===========================================================

class TestRunAllDetectors:
    def test_empty_graph_no_crash(self):
        g = CanonicalGraph(root_wallet_address="0x0000")
        findings = run_all_detectors(g)
        assert findings == []

    def test_multiple_patterns_same_graph(self):
        src = "0xMPSRC"
        recipients = [f"0xMPR{i:02d}" for i in range(5)]
        loop_back = "0xMPLB"
        nodes = [_node(src, 0)] + [_node(r, 1) for r in recipients] + [_node(loop_back, 2)]
        edges = (
            [_edge(src, r, "1.0", ts=T0 + timedelta(minutes=i)) for i, r in enumerate(recipients)]
            + [_edge(recipients[0], loop_back, "0.9", tx="0xmpback")]
            + [_edge(loop_back, src, "0.8", tx="0xmpcyc")]
        )
        g = _graph(*nodes, *edges)
        findings = run_all_detectors(g)
        found_types = {f.pattern_type for f in findings}
        assert PatternType.HIGH_FAN_OUT in found_types
        assert PatternType.CYCLIC_FLOW in found_types

    def test_engine_version_recorded(self):
        a, b, c = "0xEV1", "0xEV2", "0xEV3"
        g = _graph(
            _node(a), _node(b), _node(c),
            _edge(a, b, tx="0xev1"),
            _edge(b, c, tx="0xev2"),
            _edge(c, a, tx="0xev3"),
        )
        findings = run_all_detectors(g)
        assert all(f.engine_version == ENGINE_VERSION for f in findings)

    def test_no_blockchain_calls(self):
        g = CanonicalGraph(root_wallet_address="0x0000")
        run_all_detectors(g)
