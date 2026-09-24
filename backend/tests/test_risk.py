from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Case,
    Entity,
    EntityAddress,
    PatternRecord,
    RiskScoreRecord,
    TraceRun,
    VaspAttributionRecord,
)
from app.services.graph.model import CanonicalGraph, GraphEdge, GraphNode
from app.services.patterns.models import PatternFinding, PatternType
from app.services.risk.engine import RiskEngine
from app.services.risk.factors import RiskFactorCalculator
from app.services.risk.models import (
    DEFAULT_WEIGHTS,
    RiskCategory,
    RiskFactor,
    RiskFactorEvidence,
    RiskFactorType,
    RiskScore,
    categorize_score,
    validate_score,
)


def _node(addr: str, hop: int = 0) -> GraphNode:
    return GraphNode(id=addr, hop=hop)


def _edge(
    src: str,
    tgt: str,
    amount: str = "1.0",
    tx: str = None,
    hop: int = 0,
    timestamp: datetime = None,
) -> GraphEdge:
    return GraphEdge(
        id=f"{src}->{tgt}",
        source=src,
        target=tgt,
        transaction_hash=tx or f"0x{src[-4:]}{tgt[-4:]}",
        amount=Decimal(amount),
        timestamp=timestamp or datetime(2024, 1, 1, 12, 0, 0),
        hop=hop,
    )


def _graph(*nodes_edges) -> CanonicalGraph:
    nodes = [x for x in nodes_edges if isinstance(x, GraphNode)]
    edges = [x for x in nodes_edges if isinstance(x, GraphEdge)]
    g = CanonicalGraph(root_wallet_address=nodes[0].id if nodes else "0x0", edges=edges, nodes=nodes)
    return g.finalize()


@pytest.fixture
def mock_db_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_case():
    return Case(
        case_id=uuid4(),
        case_number="CASE-2026-000001",
        title="Test Case",
        reported_wallet_address="0xSTART",
        blockchain="ethereum",
        fraud_type="investment_scam",
        investigator_id=uuid4(),
    )


@pytest.fixture
def sample_trace(sample_case):
    return TraceRun(
        trace_id=uuid4(),
        case_id=sample_case.case_id,
        start_wallet_address="0xSTART",
        blockchain="ethereum",
    )


@pytest.fixture
def sample_entity():
    return Entity(
        entity_id=uuid4(),
        name="Tornado Cash",
        entity_type="mixer",
        jurisdiction="Decentralized",
        verification_level="verified",
    )


@pytest.fixture
def sample_entity_address(sample_entity):
    return EntityAddress(
        address_id=uuid4(),
        entity_id=sample_entity.entity_id,
        blockchain="ethereum",
        address="0xMIXER1",
        label="Tornado Cash Router",
        category="mixer_router",
        source="ofac_sanctions",
        confidence=Decimal("1.00"),
    )


@pytest.fixture
def sample_attribution(sample_case, sample_trace, sample_entity, sample_entity_address):
    attr = VaspAttributionRecord(
        attribution_id=uuid4(),
        case_id=sample_case.case_id,
        trace_id=sample_trace.trace_id,
        wallet_address="0xMIXER1",
        candidate_entity_id=sample_entity.entity_id,
        provenance_level="DIRECT",
        confidence=Decimal("1.00"),
        attribution_method="registry_exact_match",
        evidence={"match_type": "exact"},
        source="ofac_sanctions",
    )
    attr.candidate_entity = sample_entity
    return attr


# ============================================================
# RISK MODEL TESTS
# ============================================================

class TestRiskModels:
    def test_categorize_score_boundaries(self):
        assert categorize_score(0) == RiskCategory.LOW
        assert categorize_score(39) == RiskCategory.LOW
        assert categorize_score(40) == RiskCategory.MEDIUM
        assert categorize_score(69) == RiskCategory.MEDIUM
        assert categorize_score(70) == RiskCategory.HIGH
        assert categorize_score(89) == RiskCategory.HIGH
        assert categorize_score(90) == RiskCategory.CRITICAL
        assert categorize_score(100) == RiskCategory.CRITICAL

    def test_categorize_score_out_of_bounds(self):
        assert categorize_score(-10) == RiskCategory.LOW
        assert categorize_score(150) == RiskCategory.CRITICAL

    def test_validate_score_clamping(self):
        assert validate_score(-10) == 0
        assert validate_score(0) == 0
        assert validate_score(50) == 50
        assert validate_score(100) == 100
        assert validate_score(150) == 100

    def test_default_weights_structure(self):
        assert DEFAULT_WEIGHTS[RiskFactorType.KNOWN_MALICIOUS_ASSOCIATION] == 25
        assert DEFAULT_WEIGHTS[RiskFactorType.RAPID_ONWARD_TRANSFER] == 20
        assert DEFAULT_WEIGHTS[RiskFactorType.HIGH_FAN_IN] == 15
        assert DEFAULT_WEIGHTS[RiskFactorType.LAYERING_PEEL_CHAIN] == 12
        assert DEFAULT_WEIGHTS[RiskFactorType.MIXER_INTERACTION] == 10
        assert DEFAULT_WEIGHTS[RiskFactorType.REPEATED_CASE_LINKAGE] == 5
        assert sum(DEFAULT_WEIGHTS.values()) == 87


# ============================================================
# FACTOR CALCULATOR TESTS
# ============================================================

class TestRiskFactorCalculator:
    def test_known_malicious_association_mixer(self, sample_attribution):
        graph = _graph(_node("0xSTART"), _node("0xMIXER1"), _edge("0xSTART", "0xMIXER1"))
        patterns = []

        calc = RiskFactorCalculator(graph, patterns, [sample_attribution])
        factors = calc.calculate_all("0xMIXER1", include_zero_weight=True)

        malicious_factor = next(f for f in factors if f.factor_type == RiskFactorType.KNOWN_MALICIOUS_ASSOCIATION)
        assert malicious_factor.weight == 25
        assert "Tornado Cash" in malicious_factor.description

    def test_known_malicious_association_none(self):
        graph = _graph(_node("0xSTART"), _node("0xUNKNOWN"), _edge("0xSTART", "0xUNKNOWN"))
        patterns = []

        calc = RiskFactorCalculator(graph, patterns, [])
        factors = calc.calculate_all("0xUNKNOWN", include_zero_weight=True)

        malicious_factor = next(f for f in factors if f.factor_type == RiskFactorType.KNOWN_MALICIOUS_ASSOCIATION)
        assert malicious_factor.weight == 0

    def test_rapid_onward_transfer_detected(self):
        graph = _graph(
            _node("0xSTART"), _node("0xINTER"), _node("0xEND"),
            _edge("0xSTART", "0xINTER", tx="0xIN", timestamp=datetime(2024, 1, 1, 12, 0, 0)),
            _edge("0xINTER", "0xEND", tx="0xOUT", timestamp=datetime(2024, 1, 1, 12, 5, 0)),
        )
        patterns = [
            PatternFinding(
                pattern_type=PatternType.RAPID_FORWARDING,
                wallet_address="0xINTER",
                confidence=Decimal("1.00"),
                description="Forwarded 95% within 300s",
                evidence={"inbound_tx": "0xIN", "outbound_tx": "0xOUT", "time_delta_seconds": 300},
            )
        ]

        calc = RiskFactorCalculator(graph, patterns, [])
        factors = calc.calculate_all("0xINTER")

        rapid_factor = next(f for f in factors if f.factor_type == RiskFactorType.RAPID_ONWARD_TRANSFER)
        assert rapid_factor.weight == 20
        assert "0xIN" in rapid_factor.evidence.transaction_hashes
        assert "0xOUT" in rapid_factor.evidence.transaction_hashes

    def test_rapid_onward_transfer_not_detected(self):
        graph = _graph(_node("0xSTART"), _node("0xINTER"), _edge("0xSTART", "0xINTER"))
        patterns = []

        calc = RiskFactorCalculator(graph, patterns, [])
        factors = calc.calculate_all("0xINTER", include_zero_weight=True)

        rapid_factor = next(f for f in factors if f.factor_type == RiskFactorType.RAPID_ONWARD_TRANSFER)
        assert rapid_factor.weight == 0

    def test_high_fan_in_detected(self):
        graph = _graph(
            _node("0xS1"), _node("0xS2"), _node("0xS3"), _node("0xS4"), _node("0xS5"), _node("0xTGT"),
            _edge("0xS1", "0xTGT"), _edge("0xS2", "0xTGT"), _edge("0xS3", "0xTGT"),
            _edge("0xS4", "0xTGT"), _edge("0xS5", "0xTGT"),
        )
        patterns = [
            PatternFinding(
                pattern_type=PatternType.HIGH_FAN_IN,
                wallet_address="0xTGT",
                confidence=Decimal("1.00"),
                description="Received from 5 senders",
                evidence={"sender_addresses": ["0xS1", "0xS2", "0xS3", "0xS4", "0xS5"], "tx_hashes": ["0x1", "0x2", "0x3", "0x4", "0x5"]},
                metrics={"sender_count": 5},
            )
        ]

        calc = RiskFactorCalculator(graph, patterns, [])
        factors = calc.calculate_all("0xTGT")

        fan_in_factor = next(f for f in factors if f.factor_type == RiskFactorType.HIGH_FAN_IN)
        assert fan_in_factor.weight == 15
        assert len(fan_in_factor.evidence.wallet_addresses) == 5

    def test_high_fan_in_not_detected(self):
        graph = _graph(_node("0xSTART"), _node("0xTGT"), _edge("0xSTART", "0xTGT"))
        patterns = []

        calc = RiskFactorCalculator(graph, patterns, [])
        factors = calc.calculate_all("0xTGT", include_zero_weight=True)

        fan_in_factor = next(f for f in factors if f.factor_type == RiskFactorType.HIGH_FAN_IN)
        assert fan_in_factor.weight == 0

    def test_layering_peel_chain_detected(self):
        graph = _graph(
            _node("0xA"), _node("0xB"), _node("0xC"), _node("0xD"),
            _edge("0xA", "0xB"), _edge("0xB", "0xC"), _edge("0xC", "0xD"),
        )
        patterns = [
            PatternFinding(
                pattern_type=PatternType.PEEL_CHAIN,
                wallet_address="0xA",
                confidence=Decimal("1.00"),
                description="Peel chain length 4",
                evidence={"chain": ["0xA", "0xB", "0xC", "0xD"], "chain_length": 4, "tx_hashes": ["0x1", "0x2", "0x3"]},
            )
        ]

        calc = RiskFactorCalculator(graph, patterns, [])
        factors = calc.calculate_all("0xA")

        peel_factor = next(f for f in factors if f.factor_type == RiskFactorType.LAYERING_PEEL_CHAIN)
        assert peel_factor.weight == 12
        assert "Peel chain" in peel_factor.description

    def test_mixer_interaction_direct(self, sample_attribution):
        graph = _graph(_node("0xSTART"), _node("0xMIXER1"), _edge("0xSTART", "0xMIXER1"))
        patterns = []

        calc = RiskFactorCalculator(graph, patterns, [sample_attribution])
        factors = calc.calculate_all("0xMIXER1", include_zero_weight=True)

        mixer_factor = next(f for f in factors if f.factor_type == RiskFactorType.MIXER_INTERACTION)
        assert mixer_factor.weight == 10
        assert "Tornado Cash" in mixer_factor.description

    def test_mixer_interaction_via_counterparty(self, sample_attribution):
        graph = _graph(_node("0xSTART"), _node("0xINTER"), _node("0xMIXER1"), _edge("0xSTART", "0xINTER"), _edge("0xINTER", "0xMIXER1"))
        patterns = []

        calc = RiskFactorCalculator(graph, patterns, [sample_attribution])
        factors = calc.calculate_all("0xINTER", include_zero_weight=True)

        mixer_factor = next(f for f in factors if f.factor_type == RiskFactorType.MIXER_INTERACTION)
        assert mixer_factor.weight == 10
        assert "0xMIXER1" in mixer_factor.evidence.wallet_addresses

    def test_mixer_interaction_none(self):
        graph = _graph(_node("0xSTART"), _node("0xUNKNOWN"), _edge("0xSTART", "0xUNKNOWN"))
        patterns = []

        calc = RiskFactorCalculator(graph, patterns, [])
        factors = calc.calculate_all("0xUNKNOWN", include_zero_weight=True)

        mixer_factor = next(f for f in factors if f.factor_type == RiskFactorType.MIXER_INTERACTION)
        assert mixer_factor.weight == 0

    def test_repeated_case_linkage_no_db(self):
        graph = _graph(_node("0xSTART"))
        patterns = []

        calc = RiskFactorCalculator(graph, patterns, [], db_session=None)
        factors = calc.calculate_all("0xSTART", include_zero_weight=True)

        linkage_factor = next(f for f in factors if f.factor_type == RiskFactorType.REPEATED_CASE_LINKAGE)
        assert linkage_factor.weight == 0
        assert "skipped" in linkage_factor.description.lower()


# ============================================================
# RISK ENGINE TESTS
# ============================================================

@pytest.mark.asyncio
class TestRiskEngine:
    async def test_calculate_risk_basic(self, mock_db_session, sample_case, sample_trace):
        graph = _graph(
            _node("0xSTART"), _node("0xMIXER1"),
            _edge("0xSTART", "0xMIXER1", tx="0xTX1")
        )

        mock_db_session.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        mock_flush = AsyncMock()
        mock_db_session.flush = mock_flush

        engine = RiskEngine(mock_db_session)

        risk_score = await engine.calculate_risk(
            sample_case.case_id,
            sample_trace.trace_id,
            graph,
            "0xMIXER1",
        )

        assert isinstance(risk_score, RiskScore)
        assert risk_score.wallet_address == "0xMIXER1"
        assert risk_score.case_id == str(sample_case.case_id)
        assert risk_score.trace_id == str(sample_trace.trace_id)
        assert 0 <= risk_score.score <= 100
        assert risk_score.scoring_version == "v1.0.0"

    async def test_calculate_risk_deterministic(self, mock_db_session, sample_case, sample_trace):
        graph = _graph(
            _node("0xSTART"), _node("0xMIXER1"),
            _edge("0xSTART", "0xMIXER1", tx="0xTX1")
        )

        mock_db_session.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        mock_flush = AsyncMock()
        mock_db_session.flush = mock_flush

        engine = RiskEngine(mock_db_session)

        risk1 = await engine.calculate_risk(sample_case.case_id, sample_trace.trace_id, graph, "0xMIXER1")
        risk2 = await engine.calculate_risk(sample_case.case_id, sample_trace.trace_id, graph, "0xMIXER1")

        assert risk1.score == risk2.score
        assert risk1.risk_category == risk2.risk_category
        assert len(risk1.factors) == len(risk2.factors)

    async def test_get_risk_explanation(self, mock_db_session, sample_case, sample_trace):
        record = RiskScoreRecord(
            risk_score_id=uuid4(),
            case_id=sample_case.case_id,
            trace_id=sample_trace.trace_id,
            wallet_address="0xTEST",
            score=75,
            risk_category="high",
            scoring_version="v1.0.0",
            factors=[
                {
                    "factor_type": "known_malicious_association",
                    "weight": 25,
                    "evidence": {"transaction_hashes": ["0xTX1"], "entity_ids": ["ent-1"]},
                    "description": "Malicious entity",
                    "confidence": "1.00",
                },
                {
                    "factor_type": "mixer_interaction",
                    "weight": 10,
                    "evidence": {"attribution_ids": ["attr-1"]},
                    "description": "Mixer interaction",
                    "confidence": "1.00",
                },
            ],
            calculated_at=datetime.utcnow(),
        )

        mock_db_session.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = record
        mock_db_session.execute.return_value = mock_result

        engine = RiskEngine(mock_db_session)
        explanation = await engine.get_risk_explanation(sample_case.case_id, sample_trace.trace_id, "0xTEST")

        assert explanation is not None
        assert explanation.total_score == 75
        assert explanation.risk_category.value == "high"
        assert len(explanation.factor_explanations) == 2
        assert "Known Malicious Association: +25" in explanation.factor_explanations[0]
        assert "Mixer Interaction: +10" in explanation.factor_explanations[1]


# ============================================================
# INTEGRATION TESTS
# ============================================================

@pytest.mark.asyncio
class TestRiskIntegration:
    async def test_full_risk_calculation_with_patterns(self, mock_db_session, sample_case, sample_trace):
        # Create a graph that will trigger rapid forwarding AND peel chain detection
        # For peel chain: need chain of 3+ nodes each with 1 input, 2 outputs, 80%+ pass-through
        graph = _graph(
            _node("0xSTART", 0), _node("0xA", 1), _node("0xB", 2), _node("0xC", 3), _node("0xEND", 4),
            _edge("0xSTART", "0xA", "10.0", tx="0xTX1"),
            _edge("0xA", "0xB", "8.5", tx="0xTX2", timestamp=datetime(2024, 1, 1, 12, 5, 0)),
            _edge("0xA", "0xSMALL1", "1.5", tx="0xTX3"),
            _edge("0xB", "0xC", "7.5", tx="0xTX4"),
            _edge("0xB", "0xSMALL2", "1.0", tx="0xTX5"),
            _edge("0xC", "0xEND", "6.5", tx="0xTX6"),
            _edge("0xC", "0xSMALL3", "1.0", tx="0xTX7"),
        )

        mock_db_session.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        mock_flush = AsyncMock()
        mock_db_session.flush = mock_flush

        engine = RiskEngine(mock_db_session)

        risk_score = await engine.calculate_risk(
            sample_case.case_id,
            sample_trace.trace_id,
            graph,
            "0xA",
        )

        assert risk_score.score > 0
        factor_types = {f.factor_type for f in risk_score.factors}
        assert RiskFactorType.RAPID_ONWARD_TRANSFER in factor_types
        assert RiskFactorType.LAYERING_PEEL_CHAIN in factor_types

    async def test_zero_factors_empty_graph(self, mock_db_session, sample_case, sample_trace):
        graph = _graph(_node("0xISOLATED"))
        patterns = []

        mock_db_session.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        mock_flush = AsyncMock()
        mock_db_session.flush = mock_flush

        engine = RiskEngine(mock_db_session)

        risk_score = await engine.calculate_risk(
            sample_case.case_id,
            sample_trace.trace_id,
            graph,
            "0xISOLATED",
        )

        assert risk_score.score == 0
        assert risk_score.risk_category == RiskCategory.LOW
        assert all(f.weight == 0 for f in risk_score.factors)