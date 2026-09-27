from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import uuid4, UUID

import pytest
from httpx import AsyncClient

from app.main import app
from app.api.v1.traces import get_blockchain_adapter, get_trace_service
from app.db.database import get_db
from app.db.models import Case
from app.services.blockchain import (
    BlockchainAdapter,
    BlockchainErrorCode,
    CanonicalTransaction,
    TransferDirection,
    TransferFetchResult,
    TransferQuery,
)
from app.services.tracing.service import TraceService

ROOT = "0x1111111111111111111111111111111111111111"
WALLET_B = "0x2222222222222222222222222222222222222222"
CASE_ID = uuid4()


def make_case() -> Case:
    return Case(
        case_id=CASE_ID,
        case_number="CASE-2026-000001",
        title="Trace Test",
        reported_wallet_address=ROOT,
        blockchain="ethereum",
        fraud_type="investment_scam",
        investigator_id=UUID("00000000-0000-0000-0000-000000000001"),
        status="active",
    )


def make_tx(
    tx_hash: str,
    from_addr: str,
    to_addr: str,
    amount: str = "1.0",
    block: int = 100,
) -> CanonicalTransaction:
    return CanonicalTransaction(
        chain="ethereum",
        transaction_hash=tx_hash,
        block_number=block,
        block_timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        from_address=from_addr,
        to_address=to_addr,
        asset="ETH",
        amount=Decimal(amount),
        decimals=18,
        provider="fake",
        provider_reference=f"ref-{tx_hash}",
    )


class FakeAdapter(BlockchainAdapter):
    def __init__(self, error: Optional[BlockchainErrorCode] = None) -> None:
        self.error = error
        self.provider_name = "fake"

    def validate_address(self, address: str) -> str:
        return (address or "").strip().lower()

    async def fetch_transfers(self, query: TransferQuery) -> TransferFetchResult:
        if self.error is not None:
            return TransferFetchResult(
                status=self.error,
                transactions=[],
                provider=self.provider_name,
                errors=[self.error.value],
            )
        if query.direction == TransferDirection.INBOUND:
            return TransferFetchResult(
                status=BlockchainErrorCode.NO_DATA,
                transactions=[],
                provider=self.provider_name,
            )
        txs = [make_tx("0x1", query.address.lower(), WALLET_B)]
        return TransferFetchResult(
            status=BlockchainErrorCode.SUCCESS,
            transactions=txs,
            provider=self.provider_name,
            page_count=1,
        )


class StubDB:
    def __init__(self, case: Optional[Case]) -> None:
        self.case = case
        self.added = []

    def add(self, obj) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def refresh(self, obj) -> None:
        return None

    async def execute(self, *_args, **_kwargs):
        class _Result:
            def scalar_one_or_none(self_inner):
                return self.case

        return _Result()


@pytest.mark.asyncio
async def test_service_execute_trace_with_fake_adapter():
    case = make_case()
    service = TraceService({'ethereum': FakeAdapter()})
    stub = StubDB(case)
    trace = await service.execute_trace(
        db=stub,  # type: ignore[arg-type]
        case=case,
        start_wallet=ROOT,
        direction=TransferDirection.OUTBOUND,
    )
    assert trace.status in ("completed", "partial", "failed")
    assert trace.result_status is not None
    assert any(hasattr(o, "graph_data") for o in stub.added)
    assert any(hasattr(o, "transaction_hash") for o in stub.added)


@pytest.mark.asyncio
async def test_service_execute_trace_provider_failure_not_empty_success():
    case = make_case()
    service = TraceService({'ethereum': FakeAdapter(error=BlockchainErrorCode.RATE_LIMITED)})
    stub = StubDB(case)
    trace = await service.execute_trace(
        db=stub,  # type: ignore[arg-type]
        case=case,
        start_wallet=ROOT,
    )
    assert trace.status == "failed"
    assert trace.result_status == "RATE_LIMITED"
    assert trace.errors


async def _override_get_db_none():
    class _EmptyDB:
        async def execute(self, *_args, **_kwargs):
            class _Result:
                def scalar_one_or_none(self_inner):
                    return None

                def scalars(self_inner):
                    class _S:
                        def all(self_s):
                            return []
                    return _S()

            return _Result()

        def add(self, obj):
            return None

        async def flush(self):
            return None

        async def commit(self):
            return None

        async def refresh(self, obj):
            return None

    yield _EmptyDB()


@pytest.mark.asyncio
async def test_api_returns_404_for_missing_case():
    app.dependency_overrides[get_db] = _override_get_db_none
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/cases/00000000-0000-0000-0000-0000000000ff/traces",
                json={"direction": "outbound", "max_hops": 1},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert response.status_code == 404
    body = response.json()
    assert body["detail"]["error"]["code"] == "CASE_NOT_FOUND"


@pytest.mark.asyncio
async def test_api_with_overridden_dependencies_success():
    case = make_case()
    fake = FakeAdapter()

    class APIService(TraceService):
        async def get_case(self, db, case_id):
            return case if str(case.case_id) == str(case_id) else None

        async def execute_trace(
            self,
            db,
            case=None,
            case_obj=None,
            start_wallet=None,
            direction=TransferDirection.OUTBOUND,
            config=None,
            **kwargs,
        ):
            target = case or case_obj
            stub = StubDB(target)
            trace = await TraceService.execute_trace(
                self,
                stub,  # type: ignore[arg-type]
                target,
                start_wallet=start_wallet,
                direction=direction,
                config=config,
            )
            self._last_stub = stub
            return trace

    service = APIService({"ethereum": fake})

    from app.api.v1 import traces as traces_module
    from app.services.blockchain import (
        AssetType,
        TransactionStatus,
        TransactionType,
        TransferCategory,
    )

    original_load = traces_module._load_trace_payload

    async def fake_load(db, trace):
        stub = getattr(service, "_last_stub", None)
        if not stub:
            return [], None
        txs = [o for o in stub.added if hasattr(o, "provider_source")]
        graphs = [o for o in stub.added if hasattr(o, "graph_data")]
        tx_models = []
        for row in txs:
            tx_models.append(
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
                    provider=row.provider_source,
                    provider_reference=row.provider_reference,
                    raw_reference=row.raw_reference,
                )
            )
        return tx_models, graphs[0].graph_data if graphs else None

    traces_module._load_trace_payload = fake_load  # type: ignore[assignment]
    app.dependency_overrides[get_db] = _override_get_db_none
    app.dependency_overrides[get_blockchain_adapter] = lambda: fake
    app.dependency_overrides[get_trace_service] = lambda: service
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/cases/{case.case_id}/traces",
                json={"direction": "outbound", "max_hops": 1, "max_branches": 5},
            )
            assert response.status_code == 201, response.text
            data = response.json()
            assert data["case_id"] == str(case.case_id)
            assert data["status"] in ("completed", "partial")
            assert data["result_status"] in ("SUCCESS", "NO_DATA", "PARTIAL_SUCCESS")
            assert data["start_wallet_address"] == ROOT
            assert data["parameters"]["max_hops"] == 1
            assert len(data["transactions"]) == 1
            assert data["graph"] is not None
            assert data["graph"]["node_count"] >= 2
    finally:
        app.dependency_overrides.pop(get_blockchain_adapter, None)
        app.dependency_overrides.pop(get_trace_service, None)
        app.dependency_overrides.pop(get_db, None)
        traces_module._load_trace_payload = original_load  # type: ignore[assignment]
