"""Phase 5 — AI Copilot dedicated test suite.

ACCEPTANCE CATEGORIES (all 12 required, each with an explicit test in
``TestPhase5AcceptanceCategories`` below — not merely indirect coverage):

  01. successful grounded question
  02. citations in response
  03. case grounding
  04. summary generation
  05. risk explanation
  06. unsupported/insufficient data
  07. fabricated transaction hash rejection
  08. fabricated entity rejection
  09. fabricated risk-score rejection
  10. API 404/error handling
  11. provider failure handling
  12. hallucination prevention / fabricated evidence rejection

Additionally ``TestPhase5RouteContract`` verifies the three documented API
routes (POST .../copilot/ask, .../copilot/summarize, .../copilot/explain_risk)
against docs/API_CONTRACT.md section 4.10.

Section classes above provide the detailed unit coverage per category;
``TestPhase5AcceptanceCategories`` re-asserts each category end-to-end and
``test_all_12_categories_mapped`` fails if any category loses its test.
"""

import json
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from app.main import app
from app.api.v1.copilot import get_copilot_engine
from app.db.database import get_db
from app.models.copilot_schemas import (
    CopilotAskRequest,
    CopilotAskResponse,
    CopilotExplainRiskRequest,
    CopilotExplainRiskResponse,
    CopilotSummarizeResponse,
)
from app.services.ai.citations import Citation, CitationGenerator
from app.services.ai.context import ContextManager
from app.services.ai.engine import (
    CaseNotFoundError,
    CopilotEngine,
    ProviderError,
    ProviderNotConfiguredError,
)
from app.services.ai.grounding import GroundingLayer
from app.services.ai.safety import (
    HallucinationGuard,
    InsufficientDataHandler,
    ResponseType,
    SafetyCheckResult,
)
from app.services.ai.tools import create_tool_registry

CASE_ID = uuid4()
WALLET = "0x" + "1" * 40
TX_HASH = "0x" + "a" * 64
FABRICATED_TX_HASH = "0x" + "b" * 64
FABRICATED_ADDRESS = "0x" + "9" * 40

# The 12 required Phase 5 acceptance categories -> explicit test method names
ACCEPTANCE_CATEGORIES: Dict[str, str] = {
    "01_successful_grounded_question": "test_acceptance_01_successful_grounded_question",
    "02_citations_in_response": "test_acceptance_02_citations_in_response",
    "03_case_grounding": "test_acceptance_03_case_grounding",
    "04_summary_generation": "test_acceptance_04_summary_generation",
    "05_risk_explanation": "test_acceptance_05_risk_explanation",
    "06_unsupported_insufficient_data": "test_acceptance_06_unsupported_insufficient_data",
    "07_fabricated_transaction_hash_rejection": "test_acceptance_07_fabricated_transaction_hash_rejection",
    "08_fabricated_entity_rejection": "test_acceptance_08_fabricated_entity_rejection",
    "09_fabricated_risk_score_rejection": "test_acceptance_09_fabricated_risk_score_rejection",
    "10_api_404_error_handling": "test_acceptance_10_api_404_error_handling",
    "11_provider_failure_handling": "test_acceptance_11_provider_failure_handling",
    "12_hallucination_prevention_fabricated_evidence": "test_acceptance_12_hallucination_prevention_fabricated_evidence",
}


def _make_context() -> Dict[str, Any]:
    return {
        "case": {
            "case_id": str(CASE_ID),
            "case_number": "CASE-2026-000001",
            "title": "Phase 5 Test Case",
            "reported_wallet_address": WALLET,
            "reported_transaction_hash": None,
            "blockchain": "ethereum",
            "fraud_type": "investment_scam",
            "reported_amount": "1.0",
            "reported_asset": "ETH",
            "reported_date": None,
            "status": "active",
            "investigator_notes": None,
            "created_at": "2026-01-01T00:00:00",
            "updated_at": None,
        },
        "graph": None,
        "patterns": [
            {
                "pattern_id": "pat-1",
                "pattern_type": "rapid_forwarding",
                "wallet_address": WALLET,
                "confidence": "0.9",
                "description": "Funds forwarded within 10 minutes",
                "evidence": {"tx_hashes": [TX_HASH]},
                "metrics": {},
                "detected_at": "2026-01-01T00:00:00",
            }
        ],
        "attributions": [
            {
                "attribution_id": "att-1",
                "wallet_address": WALLET,
                "provenance_level": "confirmed",
                "confidence": "0.95",
                "attribution_method": "registry_match",
                "evidence": {},
                "source": "test",
                "attributed_at": "2026-01-01T00:00:00",
                "entity": {
                    "entity_id": "ent-1",
                    "name": "Binance",
                    "entity_type": "exchange",
                    "verification_level": "high",
                },
            }
        ],
        "risk_scores": [
            {
                "risk_score_id": "rs-1",
                "wallet_address": WALLET,
                "score": 75,
                "risk_category": "high",
                "scoring_version": "v1.0.0",
                "factors": [
                    {
                        "factor_type": "known_malicious_association",
                        "weight": 25,
                        "description": "Associated with known mixer",
                    },
                    {
                        "factor_type": "rapid_onward_transfer",
                        "weight": 20,
                        "description": "Funds moved within 15 minutes",
                    },
                ],
                "calculated_at": "2026-01-01T00:00:00",
            }
        ],
        "evidence": [
            {
                "evidence_id": "ev-1",
                "evidence_type": "transaction",
                "reference_id": "REF-1",
                "investigator_note": "Key transaction pinned",
                "pinned_at": "2026-01-01T00:00:00",
            }
        ],
        "transactions": [
            {
                "transaction_id": "tx-1",
                "transaction_hash": TX_HASH,
                "block_number": 100,
                "block_timestamp": "2026-01-01T00:00:00",
                "from_address": WALLET,
                "to_address": "0x" + "2" * 40,
                "asset_symbol": "ETH",
                "amount": "1.0",
                "token_contract_address": None,
                "transaction_type": "transfer",
                "status": "success",
                "discovered_at_hop": 1,
            }
        ],
        "trace_runs": [],
    }


def _make_available_data(context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "case": context.get("case", {}),
        "graph": context.get("graph"),
        "transactions": context.get("transactions", []),
        "patterns": context.get("patterns", []),
        "attributions": context.get("attributions", []),
        "risk_scores": context.get("risk_scores", []),
        "evidence": context.get("evidence", []),
    }


class StubDB:
    def __init__(self, case: Optional[Any] = None) -> None:
        self.case = case

    async def execute(self, *_args, **_kwargs):
        class _Result:
            def scalar_one_or_none(self_inner):
                return self.case

            def scalars(self_inner):
                class _S:
                    def all(self_s):
                        return []

                return _S()

        return _Result()


class FullGrounding:
    """Returns the complete fixture context for every grounding call."""

    def __init__(self, context: Dict[str, Any]) -> None:
        self._ctx = context

    async def get_case(self, case_id):
        return self._ctx["case"]

    async def get_graph(self, case_id, trace_id=None):
        return self._ctx.get("graph")

    async def get_patterns(self, case_id, trace_id=None, wallet_address=None):
        return self._ctx["patterns"]

    async def get_attributions(self, case_id, trace_id=None, wallet_address=None):
        return self._ctx["attributions"]

    async def get_risk_scores(self, case_id, trace_id=None, wallet_address=None):
        return self._ctx["risk_scores"]

    async def get_evidence(self, case_id):
        return self._ctx["evidence"]

    async def get_transactions(self, case_id, trace_id=None, limit=100):
        return self._ctx["transactions"]

    async def get_trace_runs(self, case_id):
        return self._ctx["trace_runs"]


class FakeLLMResponse:
    def __init__(self, content: str, tool_calls: Optional[list] = None) -> None:
        self.choices = [
            MagicMock(
                message=MagicMock(
                    content=content,
                    tool_calls=tool_calls or [],
                )
            )
        ]


class FakeAsyncOpenAI:
    def __init__(self, content: str = "Test answer grounded in case data.", fail: bool = False) -> None:
        self.fail = fail
        self.chat = MagicMock()
        self.chat.completions = MagicMock()
        if fail:
            self.chat.completions.create = AsyncMock(
                side_effect=Exception("simulated provider failure")
            )
        else:
            self.chat.completions.create = AsyncMock(
                return_value=FakeLLMResponse(content)
            )


def _make_engine(
    db: Any = None,
    content: str = "Test answer grounded in case data.",
    fail: bool = False,
    client: Any = None,
    grounding: Any = None,
) -> CopilotEngine:
    engine = CopilotEngine.__new__(CopilotEngine)
    engine.db = db or StubDB()
    engine.grounding = grounding or FullGrounding(_make_context())
    engine.tools = create_tool_registry(engine.db)
    engine.context_manager = ContextManager()
    engine.citation_generator = CitationGenerator()
    engine.hallucination_guard = HallucinationGuard()
    engine.insufficient_data_handler = InsufficientDataHandler()
    if client is not None:
        engine.client = client
    else:
        engine.client = FakeAsyncOpenAI(content=content, fail=fail)
    return engine


async def _override_get_db_stub():
    yield StubDB()


def _override_engine_none():
    def _dep():
        engine = _make_engine()
        engine.client = None
        engine.grounding.get_case = AsyncMock(return_value=None)
        return engine

    return _dep


def _override_engine_ok():
    def _dep():
        return _make_engine(content="Grounded answer citing case data.")

    return _dep


def _override_engine_fail():
    def _dep():
        return _make_engine(fail=True)

    return _dep


# ---------------------------------------------------------------------------
# 1. Hallucination guard — fabricated data rejection
# ---------------------------------------------------------------------------


class TestHallucinationGuard:
    def test_fabricated_transaction_hash_rejected(self):
        guard = HallucinationGuard()
        ctx = _make_available_data(_make_context())
        result = guard.check_response(
            f"Transaction {FABRICATED_TX_HASH} was observed.", ctx
        )
        assert result.allowed is False
        assert "Unverified transaction hash" in result.reason

    def test_real_transaction_hash_accepted(self):
        guard = HallucinationGuard()
        ctx = _make_available_data(_make_context())
        result = guard.check_response(f"Transaction {TX_HASH} was observed.", ctx)
        assert result.allowed is True

    def test_fabricated_entity_rejected(self):
        guard = HallucinationGuard()
        ctx = _make_available_data(_make_context())
        result = guard.check_response(
            f"Entity EvilCorp is attributed to {WALLET}.", ctx
        )
        assert result.allowed is False
        assert "Unverified entity" in result.reason

    def test_real_entity_accepted(self):
        guard = HallucinationGuard()
        ctx = _make_available_data(_make_context())
        result = guard.check_response(
            f"Entity Binance is attributed to {WALLET}.", ctx
        )
        assert result.allowed is True

    def test_fabricated_risk_score_rejected(self):
        guard = HallucinationGuard()
        ctx = _make_available_data(_make_context())
        result = guard.check_response(
            f"Risk score for {WALLET} is 95/100 (CRITICAL).", ctx
        )
        assert result.allowed is False
        assert "Unverified risk score" in result.reason

    def test_real_risk_score_accepted(self):
        guard = HallucinationGuard()
        ctx = _make_available_data(_make_context())
        result = guard.check_response(
            f"Risk score for {WALLET} is 75/100 (HIGH).", ctx
        )
        assert result.allowed is True

    def test_fabricated_pattern_rejected(self):
        guard = HallucinationGuard()
        ctx = _make_available_data(_make_context())
        result = guard.check_response("Pattern peeling_chain detected.", ctx)
        assert result.allowed is False
        assert "Unverified pattern" in result.reason

    def test_real_pattern_accepted(self):
        guard = HallucinationGuard()
        ctx = _make_available_data(_make_context())
        result = guard.check_response("Pattern rapid_forwarding detected.", ctx)
        assert result.allowed is True

    def test_fabricated_evidence_rejected(self):
        guard = HallucinationGuard()
        ctx = _make_available_data(_make_context())
        result = guard.check_response("Evidence REF-999 supports this.", ctx)
        assert result.allowed is False
        assert "Unverified evidence" in result.reason

    def test_real_evidence_accepted(self):
        guard = HallucinationGuard()
        ctx = _make_available_data(_make_context())
        result = guard.check_response("Evidence REF-1 supports this.", ctx)
        assert result.allowed is True

    def test_fabricated_address_rejected(self):
        guard = HallucinationGuard()
        ctx = _make_available_data(_make_context())
        result = guard.check_response(
            f"Address {FABRICATED_ADDRESS} received funds.", ctx
        )
        assert result.allowed is False
        assert "Unverified address" in result.reason

    def test_real_address_accepted(self):
        guard = HallucinationGuard()
        ctx = _make_available_data(_make_context())
        result = guard.check_response(
            f"Address {WALLET} received funds.", ctx
        )
        assert result.allowed is True

    def test_no_claims_allowed(self):
        guard = HallucinationGuard()
        ctx = _make_available_data(_make_context())
        result = guard.check_response("No specific claims here.", ctx)
        assert result.allowed is True

    def test_rejection_includes_suggested_response(self):
        guard = HallucinationGuard()
        ctx = _make_available_data(_make_context())
        result = guard.check_response(
            f"Transaction {FABRICATED_TX_HASH} was observed.", ctx
        )
        assert result.allowed is False
        assert result.suggested_response
        assert "sufficient verified data" in result.suggested_response


# ---------------------------------------------------------------------------
# 2. Insufficient-data handling
# ---------------------------------------------------------------------------


class TestInsufficientDataHandler:
    def test_missing_transactions_detected(self):
        handler = InsufficientDataHandler()
        missing = handler.check_data_availability({"transactions": []}, ["transactions"])
        assert missing

    def test_present_transactions_not_missing(self):
        handler = InsufficientDataHandler()
        missing = handler.check_data_availability(
            {"transactions": [{"transaction_id": "tx-1"}]}, ["transactions"]
        )
        assert not missing

    def test_risk_question_response(self):
        handler = InsufficientDataHandler()
        resp = handler.generate_response("Explain the risk score", ["risk scores"])
        assert "risk" in resp.lower()

    def test_pattern_question_response(self):
        handler = InsufficientDataHandler()
        resp = handler.generate_response("What patterns exist?", ["patterns"])
        assert "pattern" in resp.lower()

    def test_summary_question_response(self):
        handler = InsufficientDataHandler()
        resp = handler.generate_response("Summarize the case", ["transactions"])
        assert "summary" in resp.lower()

    def test_generic_question_response(self):
        handler = InsufficientDataHandler()
        resp = handler.generate_response("Tell me about the wallet", ["transactions"])
        assert "sufficient data" in resp.lower()


# ---------------------------------------------------------------------------
# 3. Context selection / truncation
# ---------------------------------------------------------------------------


class TestContextManager:
    def test_priority_order_matches_spec(self):
        cm = ContextManager()
        assert cm.PRIORITY_ORDER == [
            "case_metadata",
            "transactions",
            "patterns",
            "attributions",
            "risk_factors",
            "evidence",
        ]

    def test_truncation_fires_within_budget(self):
        cm = ContextManager(max_tokens=2000)
        case = _make_context()["case"]
        txs = _make_context()["transactions"] * 500
        ctx = cm.build_context(case_data=case, transactions=txs)
        total = sum(cm.estimate_tokens(v) for v in ctx.values())
        assert total <= cm.available_tokens

    def test_case_metadata_always_included(self):
        cm = ContextManager()
        case = _make_context()["case"]
        ctx = cm.build_context(case_data=case)
        assert "case_metadata" in ctx

    def test_estimated_tokens_positive(self):
        cm = ContextManager()
        assert cm.estimate_tokens("hello") >= 1


# ---------------------------------------------------------------------------
# 4. Citation generation / validation
# ---------------------------------------------------------------------------


class TestCitations:
    def test_valid_citation_passes(self):
        gen = CitationGenerator()
        tx = _make_context()["transactions"][0]
        c = gen.create_transaction_citation(tx)
        avail = _make_available_data(_make_context())
        assert gen.validate_citation(c, avail) is True

    def test_fabricated_citation_rejected(self):
        gen = CitationGenerator()
        fake = Citation(type="transaction", reference_id="0xfake", summary="fake")
        avail = _make_available_data(_make_context())
        assert gen.validate_citation(fake, avail) is False

    def test_filter_removes_fabricated(self):
        gen = CitationGenerator()
        tx = _make_context()["transactions"][0]
        real = gen.create_transaction_citation(tx)
        fake = Citation(type="transaction", reference_id="0xfake", summary="fake")
        avail = _make_available_data(_make_context())
        filtered = gen.filter_valid_citations([real, fake], avail)
        assert len(filtered) == 1
        assert filtered[0].reference_id == real.reference_id

    def test_case_citation_created(self):
        gen = CitationGenerator()
        case = _make_context()["case"]
        c = gen.create_case_citation(case)
        assert c.type == "case"
        assert c.reference_id == str(CASE_ID)

    def test_pattern_citation_created(self):
        gen = CitationGenerator()
        p = _make_context()["patterns"][0]
        c = gen.create_pattern_citation(p)
        assert c.type == "pattern"

    def test_attribution_citation_created(self):
        gen = CitationGenerator()
        a = _make_context()["attributions"][0]
        c = gen.create_attribution_citation(a)
        assert c.type == "attribution"

    def test_risk_factor_citation_created(self):
        gen = CitationGenerator()
        r = _make_context()["risk_scores"][0]
        c = gen.create_risk_factor_citation(r, "known_malicious_association")
        assert c.type == "risk_factor"

    def test_evidence_citation_created(self):
        gen = CitationGenerator()
        e = _make_context()["evidence"][0]
        c = gen.create_evidence_citation(e)
        assert c.type == "evidence"


# ---------------------------------------------------------------------------
# 5. Copilot orchestration — successful grounded question
# ---------------------------------------------------------------------------


class TestCopilotOrchestration:
    @pytest.mark.asyncio
    async def test_successful_grounded_question(self):
        engine = _make_engine()
        result = await engine.ask(CASE_ID, "What is the reported wallet?")
        assert result["type"] == ResponseType.ANSWER.value
        assert result["answer"]
        assert isinstance(result["citations"], list)
        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_citations_in_answer(self):
        engine = _make_engine()
        result = await engine.ask(CASE_ID, "What transactions exist?")
        assert "citations" in result
        assert isinstance(result["citations"], list)

    @pytest.mark.asyncio
    async def test_case_grounding_builds_context(self):
        engine = _make_engine()
        context = await engine._build_context(CASE_ID)
        assert context["case"]["case_id"] == str(CASE_ID)
        assert context["transactions"]
        assert context["patterns"]
        assert context["attributions"]
        assert context["risk_scores"]
        assert context["evidence"]

    @pytest.mark.asyncio
    async def test_summary_generation(self):
        engine = _make_engine()
        result = await engine.summarize(CASE_ID)
        assert result["type"] == ResponseType.ANSWER.value
        assert result["answer"]

    @pytest.mark.asyncio
    async def test_risk_explanation(self):
        engine = _make_engine()
        result = await engine.explain_risk(CASE_ID, WALLET)
        assert result["type"] == ResponseType.ANSWER.value
        assert result["answer"]

    @pytest.mark.asyncio
    async def test_insufficient_data_no_transactions(self):
        empty_ctx = _make_context()
        empty_ctx["transactions"] = []
        engine = _make_engine(grounding=FullGrounding(empty_ctx))
        result = await engine.ask(CASE_ID, "What patterns exist?")
        assert result["type"] == ResponseType.INSUFFICIENT_DATA.value
        assert "sufficient data" in result["answer"].lower() or "cannot" in result["answer"].lower()

    @pytest.mark.asyncio
    async def test_nonexistent_case_raises_case_not_found(self):
        empty_ctx = _make_context()
        engine = _make_engine(grounding=FullGrounding(empty_ctx))
        engine.grounding.get_case = AsyncMock(return_value=None)
        with pytest.raises(CaseNotFoundError):
            await engine._build_context(CASE_ID)

    @pytest.mark.asyncio
    async def test_provider_failure_raises_provider_error(self):
        engine = _make_engine(fail=True)
        with pytest.raises(ProviderError):
            await engine.ask(CASE_ID, "What is the wallet?")

    @pytest.mark.asyncio
    async def test_provider_not_configured_raises(self):
        engine = _make_engine()
        engine.client = None
        with pytest.raises(ProviderNotConfiguredError):
            await engine.ask(CASE_ID, "What is the wallet?")

    @pytest.mark.asyncio
    async def test_hallucinated_response_replaced(self):
        fabricated = f"Transaction {FABRICATED_TX_HASH} moved 10 ETH to {FABRICATED_ADDRESS}."
        engine = _make_engine(content=fabricated)
        result = await engine.ask(CASE_ID, "What happened?")
        assert "sufficient verified data" in result["answer"].lower() or result["answer"] != fabricated

    @pytest.mark.asyncio
    async def test_context_to_available_data_includes_case_and_graph(self):
        engine = _make_engine()
        context = await engine._build_context(CASE_ID)
        avail = engine._context_to_available_data(context)
        assert "case" in avail
        assert "graph" in avail
        assert "transactions" in avail


# ---------------------------------------------------------------------------
# 6. API endpoint tests — 404, 503, 502, validation, success
# ---------------------------------------------------------------------------


class TestCopilotAPI:
    @pytest.mark.asyncio
    async def test_ask_nonexistent_case_returns_404(self):
        app.dependency_overrides[get_db] = _override_get_db_stub
        app.dependency_overrides[get_copilot_engine] = _override_engine_none()
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/cases/{uuid4()}/copilot/ask",
                    json={"question": "What is the wallet?"},
                )
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.dependency_overrides.pop(get_copilot_engine, None)
        assert response.status_code == 404
        body = response.json()
        assert body["detail"]["error"]["code"] == "CASE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_summarize_nonexistent_case_returns_404(self):
        app.dependency_overrides[get_db] = _override_get_db_stub
        app.dependency_overrides[get_copilot_engine] = _override_engine_none()
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/cases/{uuid4()}/copilot/summarize"
                )
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.dependency_overrides.pop(get_copilot_engine, None)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_explain_risk_nonexistent_case_returns_404(self):
        app.dependency_overrides[get_db] = _override_get_db_stub
        app.dependency_overrides[get_copilot_engine] = _override_engine_none()
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/cases/{uuid4()}/copilot/explain_risk",
                    json={"wallet_address": WALLET},
                )
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.dependency_overrides.pop(get_copilot_engine, None)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_provider_not_configured_returns_503(self):
        engine = _make_engine()
        engine.client = None

        def _dep():
            return engine

        app.dependency_overrides[get_db] = _override_get_db_stub
        app.dependency_overrides[get_copilot_engine] = _dep
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/cases/{CASE_ID}/copilot/ask",
                    json={"question": "What is the wallet?"},
                )
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.dependency_overrides.pop(get_copilot_engine, None)
        assert response.status_code == 503
        body = response.json()
        assert body["detail"]["error"]["code"] == "PROVIDER_NOT_CONFIGURED"

    @pytest.mark.asyncio
    async def test_provider_failure_returns_502(self):
        app.dependency_overrides[get_db] = _override_get_db_stub
        app.dependency_overrides[get_copilot_engine] = _override_engine_fail()
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/cases/{CASE_ID}/copilot/ask",
                    json={"question": "What is the wallet?"},
                )
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.dependency_overrides.pop(get_copilot_engine, None)
        assert response.status_code == 502
        body = response.json()
        assert body["detail"]["error"]["code"] == "PROVIDER_ERROR"

    @pytest.mark.asyncio
    async def test_invalid_wallet_address_returns_422(self):
        app.dependency_overrides[get_db] = _override_get_db_stub
        app.dependency_overrides[get_copilot_engine] = _override_engine_ok()
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/cases/{CASE_ID}/copilot/explain_risk",
                    json={"wallet_address": "not-a-wallet"},
                )
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.dependency_overrides.pop(get_copilot_engine, None)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_question_returns_422(self):
        app.dependency_overrides[get_db] = _override_get_db_stub
        app.dependency_overrides[get_copilot_engine] = _override_engine_ok()
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/cases/{CASE_ID}/copilot/ask",
                    json={"question": ""},
                )
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.dependency_overrides.pop(get_copilot_engine, None)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_successful_ask_returns_200_with_citations(self):
        app.dependency_overrides[get_db] = _override_get_db_stub
        app.dependency_overrides[get_copilot_engine] = _override_engine_ok()
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/cases/{CASE_ID}/copilot/ask",
                    json={"question": "What is the reported wallet?"},
                )
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.dependency_overrides.pop(get_copilot_engine, None)
        assert response.status_code == 200
        body = response.json()
        CopilotAskResponse(**body)
        assert body["answer"]
        assert isinstance(body["citations"], list)

    @pytest.mark.asyncio
    async def test_successful_summarize_returns_200(self):
        app.dependency_overrides[get_db] = _override_get_db_stub
        app.dependency_overrides[get_copilot_engine] = _override_engine_ok()
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/cases/{CASE_ID}/copilot/summarize"
                )
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.dependency_overrides.pop(get_copilot_engine, None)
        assert response.status_code == 200
        body = response.json()
        CopilotSummarizeResponse(**body)

    @pytest.mark.asyncio
    async def test_successful_explain_risk_returns_200(self):
        app.dependency_overrides[get_db] = _override_get_db_stub
        app.dependency_overrides[get_copilot_engine] = _override_engine_ok()
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/cases/{CASE_ID}/copilot/explain_risk",
                    json={"wallet_address": WALLET},
                )
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.dependency_overrides.pop(get_copilot_engine, None)
        assert response.status_code == 200
        body = response.json()
        CopilotExplainRiskResponse(**body)


# ---------------------------------------------------------------------------
# 7. Tool registry
# ---------------------------------------------------------------------------


class TestToolRegistry:
    def test_all_approved_tools_registered(self):
        registry = create_tool_registry(StubDB())
        names = {t["name"] for t in registry.list_tools()}
        required = {
            "get_case",
            "get_graph",
            "get_patterns",
            "get_attributions",
            "get_risk",
            "get_evidence",
        }
        assert required.issubset(names)

    def test_openai_functions_format(self):
        registry = create_tool_registry(StubDB())
        funcs = registry.get_openai_functions()
        assert all("name" in f and "description" in f and "parameters" in f for f in funcs)


# ---------------------------------------------------------------------------
# 8. Grounding layer
# ---------------------------------------------------------------------------


class TestGroundingLayer:
    def test_required_methods_exist(self):
        methods = [
            "get_case",
            "get_graph",
            "get_patterns",
            "get_attributions",
            "get_risk_scores",
            "get_evidence",
            "get_transactions",
            "get_trace_runs",
        ]
        for m in methods:
            assert hasattr(GroundingLayer, m), f"missing {m}"


# ---------------------------------------------------------------------------
# 9. Provider configuration isolation
# ---------------------------------------------------------------------------


class TestProviderConfiguration:
    def test_no_hardcoded_api_key_in_engine_source(self):
        import inspect
        from app.services.ai import engine as engine_module

        source = inspect.getsource(engine_module)
        assert "sk-" not in source

    def test_api_key_from_settings_only(self):
        from app.config import settings

        assert hasattr(settings, "openai_api_key")
        assert isinstance(settings.openai_api_key, (str, type(None)))


# ---------------------------------------------------------------------------
# 10. Documented API route contract (docs/API_CONTRACT.md section 4.10)
# ---------------------------------------------------------------------------


class TestPhase5RouteContract:
    EXPECTED_ROUTES = {
        "/api/v1/cases/{case_id}/copilot/ask",
        "/api/v1/cases/{case_id}/copilot/summarize",
        "/api/v1/cases/{case_id}/copilot/explain_risk",
    }

    def _post_routes(self) -> Dict[str, set]:
        routes: Dict[str, set] = {}
        for route in app.routes:
            methods = getattr(route, "methods", None) or set()
            path = getattr(route, "path", None)
            if path:
                routes[path] = {m.upper() for m in methods}
        return routes

    def test_all_three_documented_routes_registered(self):
        routes = self._post_routes()
        for expected in self.EXPECTED_ROUTES:
            assert expected in routes, f"missing documented route: {expected}"

    def test_all_three_routes_accept_post(self):
        routes = self._post_routes()
        for expected in self.EXPECTED_ROUTES:
            assert "POST" in routes.get(expected, set()), f"{expected} is not POST"

    def test_no_undocumented_copilot_routes(self):
        routes = self._post_routes()
        copilot_paths = {p for p in routes if "/copilot/" in p}
        assert copilot_paths == self.EXPECTED_ROUTES


# ---------------------------------------------------------------------------
# 11. EXPLICIT PHASE 5 ACCEPTANCE CATEGORIES (12 required categories)
# ---------------------------------------------------------------------------


class TestPhase5AcceptanceCategories:
    """One explicit test per required Phase 5 acceptance category.

    ACCEPTANCE_CATEGORIES maps each category key to its test method name;
    ``test_all_12_categories_mapped`` guarantees none is missing or renamed.
    """

    def test_all_12_categories_mapped(self):
        assert len(ACCEPTANCE_CATEGORIES) == 12
        for category, method_name in ACCEPTANCE_CATEGORIES.items():
            assert hasattr(self, method_name), f"category {category} has no test"
            assert callable(getattr(self, method_name))

    @pytest.mark.asyncio
    async def test_acceptance_01_successful_grounded_question(self):
        engine = _make_engine(content="The reported wallet is the case subject.")
        result = await engine.ask(CASE_ID, "What is the reported wallet?")
        assert result["type"] == ResponseType.ANSWER.value
        assert result["answer"]
        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_acceptance_02_citations_in_response(self):
        engine = _make_engine(content="The reported wallet is the case subject. [0]")
        result = await engine.ask(CASE_ID, "What transactions exist?")
        assert isinstance(result["citations"], list)
        assert result["citations"], "grounded answer must include citations"
        gen = CitationGenerator()
        avail = engine._context_to_available_data(await engine._build_context(CASE_ID))
        for c in result["citations"]:
            assert {"type", "reference_id", "summary"} <= set(c.keys())
            assert gen.validate_citation(
                Citation(type=c["type"], reference_id=c["reference_id"], summary=c["summary"]),
                avail,
            ), f"citation not validated against case data: {c}"

    @pytest.mark.asyncio
    async def test_acceptance_03_case_grounding(self):
        engine = _make_engine()
        context = await engine._build_context(CASE_ID)
        assert context["case"]["case_id"] == str(CASE_ID)
        assert context["transactions"]
        assert context["patterns"]
        assert context["attributions"]
        assert context["risk_scores"]
        assert context["evidence"]

    @pytest.mark.asyncio
    async def test_acceptance_04_summary_generation(self):
        engine = _make_engine(content="Case summary grounded in trace data.")
        result = await engine.summarize(CASE_ID)
        assert result["type"] == ResponseType.ANSWER.value
        assert result["answer"]

    @pytest.mark.asyncio
    async def test_acceptance_05_risk_explanation(self):
        engine = _make_engine(content="Risk is driven by malicious association and fast forwarding.")
        result = await engine.explain_risk(CASE_ID, WALLET)
        assert result["type"] == ResponseType.ANSWER.value
        assert result["answer"]

    @pytest.mark.asyncio
    async def test_acceptance_06_unsupported_insufficient_data(self):
        empty_ctx = _make_context()
        empty_ctx["transactions"] = []
        engine = _make_engine(grounding=FullGrounding(empty_ctx))
        result = await engine.ask(CASE_ID, "What patterns exist?")
        assert result["type"] == ResponseType.INSUFFICIENT_DATA.value
        assert result["confidence"] == 0.0
        answer_lower = result["answer"].lower()
        assert "sufficient data" in answer_lower or "cannot" in answer_lower

    def test_acceptance_07_fabricated_transaction_hash_rejection(self):
        guard = HallucinationGuard()
        ctx = _make_available_data(_make_context())
        result = guard.check_response(f"Transaction {FABRICATED_TX_HASH} moved funds.", ctx)
        assert result.allowed is False
        assert "Unverified transaction hash" in result.reason
        control = guard.check_response(f"Transaction {TX_HASH} moved funds.", ctx)
        assert control.allowed is True

    def test_acceptance_08_fabricated_entity_rejection(self):
        guard = HallucinationGuard()
        ctx = _make_available_data(_make_context())
        result = guard.check_response(f"Entity EvilCorp is attributed to {WALLET}.", ctx)
        assert result.allowed is False
        assert "Unverified entity" in result.reason
        control = guard.check_response(f"Entity Binance is attributed to {WALLET}.", ctx)
        assert control.allowed is True

    def test_acceptance_09_fabricated_risk_score_rejection(self):
        guard = HallucinationGuard()
        ctx = _make_available_data(_make_context())
        result = guard.check_response(f"Risk score for {WALLET} is 99/100.", ctx)
        assert result.allowed is False
        assert "Unverified risk score" in result.reason
        control = guard.check_response(f"Risk score for {WALLET} is 75/100.", ctx)
        assert control.allowed is True

    @pytest.mark.asyncio
    async def test_acceptance_10_api_404_error_handling(self):
        app.dependency_overrides[get_db] = _override_get_db_stub
        app.dependency_overrides[get_copilot_engine] = _override_engine_none()
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/cases/{uuid4()}/copilot/ask",
                    json={"question": "What is the wallet?"},
                )
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.dependency_overrides.pop(get_copilot_engine, None)
        assert response.status_code == 404
        body = response.json()
        assert body["detail"]["error"]["code"] == "CASE_NOT_FOUND"
        assert body["detail"]["error"]["message"]

    @pytest.mark.asyncio
    async def test_acceptance_11_provider_failure_handling(self):
        engine = _make_engine(fail=True)
        with pytest.raises(ProviderError):
            await engine.ask(CASE_ID, "What is the wallet?")

        app.dependency_overrides[get_db] = _override_get_db_stub
        app.dependency_overrides[get_copilot_engine] = _override_engine_fail()
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/cases/{CASE_ID}/copilot/ask",
                    json={"question": "What is the wallet?"},
                )
        finally:
            app.dependency_overrides.pop(get_db, None)
            app.dependency_overrides.pop(get_copilot_engine, None)
        assert response.status_code == 502
        assert response.json()["detail"]["error"]["code"] == "PROVIDER_ERROR"

    @pytest.mark.asyncio
    async def test_acceptance_12_hallucination_prevention_fabricated_evidence(self):
        guard = HallucinationGuard()
        ctx = _make_available_data(_make_context())
        evidence_result = guard.check_response("Evidence REF-999 supports this claim.", ctx)
        assert evidence_result.allowed is False
        assert "Unverified evidence" in evidence_result.reason

        fabricated = (
            f"Transaction {FABRICATED_TX_HASH} moved funds to {FABRICATED_ADDRESS}. "
            "Evidence REF-999 confirms it."
        )
        engine = _make_engine(content=fabricated)
        result = await engine.ask(CASE_ID, "What happened?")
        assert result["answer"] != fabricated
        assert "sufficient verified data" in result["answer"].lower()
        gen = CitationGenerator()
        for c in result["citations"]:
            assert gen.validate_citation(
                Citation(type=c["type"], reference_id=c["reference_id"], summary=c["summary"]),
                engine._context_to_available_data(await engine._build_context(CASE_ID)),
            )
