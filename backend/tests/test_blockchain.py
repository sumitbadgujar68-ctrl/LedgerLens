import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

import httpx
import pytest

from app.services.blockchain.adapter import EthereumAdapter, is_valid_ethereum_address
from app.services.blockchain.canonical import (
    AssetType,
    TransferCategory,
    TransferDirection,
    TransferFetchResult,
    TransferQuery,
)
from app.services.blockchain.errors import (
    BlockchainErrorCode,
    ProviderResponseError,
    RateLimitError,
    ProviderUnavailableError,
)
from app.services.blockchain.normalizer import TransactionNormalizer
from app.services.blockchain.providers.alchemy import AlchemyProvider
from app.services.blockchain.providers.base import EthereumProvider, ProviderPage, ProviderTransfer

VALID_ADDRESS = "0x1111111111111111111111111111111111111111"
VALID_ADDRESS_2 = "0x2222222222222222222222222222222222222222"


def make_transfer(
    tx_hash: str,
    amount_raw: str,
    decimals: int = 18,
    category: TransferCategory = TransferCategory.EXTERNAL,
    block_number: int = 100,
    from_address: str = VALID_ADDRESS,
    to_address: str = VALID_ADDRESS_2,
) -> ProviderTransfer:
    return ProviderTransfer(
        provider="fake",
        chain="ethereum",
        transaction_hash=tx_hash,
        block_number=block_number,
        block_timestamp=datetime(2026, 1, 1, 12, 0, 0),
        from_address=from_address,
        to_address=to_address,
        asset_symbol="ETH" if category == TransferCategory.EXTERNAL else "USDT",
        token_contract=None if category == TransferCategory.EXTERNAL else "0xdac17f958d2ee523a2206206994597c13d831ec7",
        amount_raw=amount_raw,
        decimals=decimals,
        transfer_category=category,
        provider_reference=f"ref-{tx_hash}",
        raw_reference=f"block={block_number}",
        raw={"hash": tx_hash},
    )


class FakeEthereumProvider(EthereumProvider):
    name = "fake"

    def __init__(
        self,
        pages: Optional[List[ProviderPage]] = None,
        error: Optional[Exception] = None,
    ) -> None:
        self.pages = pages or [ProviderPage(provider=self.name, transfers=[], page_key=None)]
        self.error = error
        self.calls: List[Dict] = []

    async def get_asset_transfers(self, **kwargs) -> ProviderPage:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        index = kwargs.get("_page_index", 0)
        # page_key encoding: first call no key -> page 0; subsequent uses returned key
        page_key = kwargs.get("page_key")
        if page_key is None:
            return self.pages[0]
        try:
            idx = int(page_key)
        except ValueError:
            return ProviderPage(provider=self.name, transfers=[], page_key=None)
        if idx < 0 or idx >= len(self.pages):
            return ProviderPage(provider=self.name, transfers=[], page_key=None)
        return self.pages[idx]


class SequenceProvider(EthereumProvider):
    name = "sequence"

    def __init__(self, pages: List[ProviderPage], error: Optional[Exception] = None, fail_after: Optional[int] = None) -> None:
        self._pages = pages
        self._error = error
        self._fail_after = fail_after
        self.calls = 0

    async def get_asset_transfers(self, **kwargs) -> ProviderPage:
        self.calls += 1
        if self._fail_after is not None and self.calls > self._fail_after and self._error is not None:
            raise self._error
        if self._error is not None and self._fail_after is None:
            raise self._error
        idx = kwargs.get("_idx")
        if idx is None:
            page_key = kwargs.get("page_key")
            idx = int(page_key) if page_key is not None else 0
        if idx < 0 or idx >= len(self._pages):
            return ProviderPage(provider=self.name, transfers=[], page_key=None)
        return self._pages[idx]


def test_valid_ethereum_address():
    assert is_valid_ethereum_address(VALID_ADDRESS)
    assert is_valid_ethereum_address("0xABCDEFabcdefABCDEFabcdefABCDEFabcdefABCD")
    assert not is_valid_ethereum_address("0x123")
    assert not is_valid_ethereum_address("")
    assert not is_valid_ethereum_address("not-an-address")


def test_adapter_rejects_invalid_address():
    adapter = EthereumAdapter(provider=FakeEthereumProvider())

    import asyncio

    result = asyncio.get_event_loop().run_until_complete(
        adapter.fetch_transfers(TransferQuery(address="bad-address"))
    )
    assert result.status == BlockchainErrorCode.INVALID_INPUT
    assert result.transactions == []


def test_normalizer_decimal_precision_large_amount():
    normalizer = TransactionNormalizer()
    # 1,000,000.000000000000000001 tokens with 18 decimals
    # amount_raw = 1000000.000000000000000001 * 10^18 = 10^24 + 1
    transfer = make_transfer(
        "0xabc",
        amount_raw="1000000000000000000000001",
        decimals=18,
        category=TransferCategory.ERC20,
    )
    canonical = normalizer.normalize(transfer)
    assert canonical.amount == Decimal("1000000.000000000000000001")
    assert canonical.asset_type == AssetType.ERC20
    assert isinstance(canonical.amount, Decimal)


def test_normalizer_native_eth_amount():
    normalizer = TransactionNormalizer()
    transfer = make_transfer("0xdef", amount_raw=str(int(1.5 * 10**18)), decimals=18)
    canonical = normalizer.normalize(transfer)
    assert canonical.amount == Decimal("1.5")
    assert canonical.asset_type == AssetType.NATIVE
    assert canonical.from_address == VALID_ADDRESS.lower()


def test_normalizer_preserves_provenance():
    normalizer = TransactionNormalizer()
    transfer = make_transfer("0xaaa", amount_raw="1000000", decimals=6, category=TransferCategory.ERC20)
    canonical = normalizer.normalize(transfer)
    assert canonical.provider == "fake"
    assert canonical.provider_reference == "ref-0xaaa"
    assert canonical.raw_reference is not None
    assert canonical.chain == "ethereum"


def test_alchemy_provider_parses_response():
    api_key = "test-key"
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "transfers": [
                {
                    "blockNum": "0x10",
                    "hash": "0xhash1",
                    "from": VALID_ADDRESS,
                    "to": VALID_ADDRESS_2,
                    "value": 1.0,
                    "asset": "ETH",
                    "category": "external",
                    "uniqueId": "uid-1",
                    "rawContract": {"value": hex(10**18), "address": None, "decimal": None},
                    "metadata": {"blockTimestamp": "2026-01-01T00:00:00.000Z"},
                }
            ],
            "pageKey": "next-page",
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/v2/test-key")
        payload = json.loads(request.content)
        assert payload["method"] == "alchemy_getAssetTransfers"
        assert payload["params"][0]["fromAddress"] == VALID_ADDRESS
        return httpx.Response(200, json=body)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = AlchemyProvider(api_key=api_key, client=client)

    import asyncio

    page = asyncio.get_event_loop().run_until_complete(
        provider.get_asset_transfers(from_address=VALID_ADDRESS, max_count=100)
    )
    assert page.page_key == "next-page"
    assert len(page.transfers) == 1
    tx = page.transfers[0]
    assert tx.block_number == 16
    assert tx.amount_raw == str(10**18)
    assert tx.decimals == 18
    assert tx.transfer_category == TransferCategory.EXTERNAL
    assert tx.block_timestamp is not None


def test_alchemy_provider_rate_limit_http_429():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="rate limited")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = AlchemyProvider(api_key="secret-key", client=client)

    import asyncio

    with pytest.raises(RateLimitError):
        asyncio.get_event_loop().run_until_complete(
            provider.get_asset_transfers(from_address=VALID_ADDRESS)
        )


def test_alchemy_provider_masks_api_key_in_errors():
    api_key = "super-secret-key"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text=f"failure at https://eth-mainnet.g.alchemy.com/v2/{api_key}")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = AlchemyProvider(api_key=api_key, client=client)

    import asyncio

    with pytest.raises(ProviderUnavailableError) as exc_info:
        asyncio.get_event_loop().run_until_complete(
            provider.get_asset_transfers(from_address=VALID_ADDRESS)
        )
    assert api_key not in str(exc_info.value)
    assert "***" in str(exc_info.value)


def test_alchemy_provider_rpc_rate_limit_error_body():
    body = {"jsonrpc": "2.0", "id": 1, "error": {"code": -32000, "message": "Rate limit exceeded"}}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = AlchemyProvider(api_key="k", client=client)

    import asyncio

    with pytest.raises(RateLimitError):
        asyncio.get_event_loop().run_until_complete(
            provider.get_asset_transfers(from_address=VALID_ADDRESS)
        )


def test_alchemy_provider_invalid_transfers_shape():
    body = {"jsonrpc": "2.0", "id": 1, "result": {"transfers": "not-a-list"}}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = AlchemyProvider(api_key="k", client=client)

    import asyncio

    with pytest.raises(ProviderResponseError):
        asyncio.get_event_loop().run_until_complete(
            provider.get_asset_transfers(from_address=VALID_ADDRESS)
        )


def test_pagination_traverses_all_pages():
    page0 = ProviderPage(
        provider="sequence",
        transfers=[make_transfer("0x1", "1000000000000000000", block_number=1)],
        page_key="1",
    )
    page1 = ProviderPage(
        provider="sequence",
        transfers=[make_transfer("0x2", "1000000000000000000", block_number=2)],
        page_key="2",
    )
    page2 = ProviderPage(
        provider="sequence",
        transfers=[make_transfer("0x3", "1000000000000000000", block_number=3)],
        page_key=None,
    )
    provider = SequenceProvider([page0, page1, page2])
    adapter = EthereumAdapter(provider=provider)

    import asyncio

    result = asyncio.get_event_loop().run_until_complete(
        adapter.fetch_transfers(TransferQuery(address=VALID_ADDRESS, direction=TransferDirection.OUTBOUND))
    )
    assert result.status == BlockchainErrorCode.SUCCESS
    assert len(result.transactions) == 3
    assert result.page_count == 3
    assert result.has_more is False


def test_pagination_respects_max_pages():
    pages = []
    for i in range(5):
        pages.append(
            ProviderPage(
                provider="sequence",
                transfers=[make_transfer(f"0x{i}", "1", block_number=i)],
                page_key=str(i + 1) if i < 4 else None,
            )
        )
    provider = SequenceProvider(pages)
    adapter = EthereumAdapter(provider=provider)

    import asyncio

    result = asyncio.get_event_loop().run_until_complete(
        adapter.fetch_transfers(
            TransferQuery(
                address=VALID_ADDRESS,
                direction=TransferDirection.OUTBOUND,
                max_pages=2,
            )
        )
    )
    assert result.page_count == 2
    assert result.has_more is True
    assert any("page_limit_reached" in e for e in result.errors)
    assert result.status in (BlockchainErrorCode.SUCCESS, BlockchainErrorCode.PARTIAL_SUCCESS)


def test_rate_limit_with_no_data_is_not_empty_success():
    provider = SequenceProvider([], error=RateLimitError("rate limited"))
    adapter = EthereumAdapter(provider=provider)

    import asyncio

    result = asyncio.get_event_loop().run_until_complete(
        adapter.fetch_transfers(TransferQuery(address=VALID_ADDRESS, direction=TransferDirection.OUTBOUND))
    )
    assert result.status == BlockchainErrorCode.RATE_LIMITED
    assert result.transactions == []
    assert result.errors


def test_rate_limit_after_partial_data_is_partial_success():
    page0 = ProviderPage(
        provider="sequence",
        transfers=[make_transfer("0x1", "1")],
        page_key="1",
    )
    provider = SequenceProvider(
        [page0],
        error=RateLimitError("rate limited"),
        fail_after=1,
    )
    adapter = EthereumAdapter(provider=provider)

    import asyncio

    result = asyncio.get_event_loop().run_until_complete(
        adapter.fetch_transfers(TransferQuery(address=VALID_ADDRESS, direction=TransferDirection.OUTBOUND))
    )
    assert result.status == BlockchainErrorCode.PARTIAL_SUCCESS
    assert len(result.transactions) == 1
    assert any("rate limited" in e for e in result.errors)


def test_provider_unavailable_maps_status():
    provider = SequenceProvider([], error=ProviderUnavailableError("provider down"))
    adapter = EthereumAdapter(provider=provider)

    import asyncio

    result = asyncio.get_event_loop().run_until_complete(
        adapter.fetch_transfers(TransferQuery(address=VALID_ADDRESS, direction=TransferDirection.OUTBOUND))
    )
    assert result.status == BlockchainErrorCode.PROVIDER_UNAVAILABLE
    assert result.transactions == []


def test_no_data_status():
    provider = SequenceProvider([ProviderPage(provider="sequence", transfers=[], page_key=None)])
    adapter = EthereumAdapter(provider=provider)

    import asyncio

    result = asyncio.get_event_loop().run_until_complete(
        adapter.fetch_transfers(TransferQuery(address=VALID_ADDRESS, direction=TransferDirection.OUTBOUND))
    )
    assert result.status == BlockchainErrorCode.NO_DATA
    assert result.transactions == []


def test_invalid_input_status_from_provider():
    provider = SequenceProvider([], error=ProviderResponseError("bad response"))
    adapter = EthereumAdapter(provider=provider)

    import asyncio

    result = asyncio.get_event_loop().run_until_complete(
        adapter.fetch_transfers(TransferQuery(address=VALID_ADDRESS, direction=TransferDirection.OUTBOUND))
    )
    assert result.status == BlockchainErrorCode.FAILED
    assert result.errors


def test_both_directions_merge_dedup():
    outbound = ProviderPage(
        provider="sequence",
        transfers=[
            make_transfer("0xshared", "1", from_address=VALID_ADDRESS, to_address=VALID_ADDRESS_2, block_number=10),
            make_transfer("0xout", "1", from_address=VALID_ADDRESS, to_address=VALID_ADDRESS_2, block_number=11),
        ],
        page_key=None,
    )
    inbound = ProviderPage(
        provider="sequence",
        transfers=[
            make_transfer("0xshared", "1", from_address=VALID_ADDRESS, to_address=VALID_ADDRESS_2, block_number=10),
            make_transfer("0xin", "1", from_address=VALID_ADDRESS_2, to_address=VALID_ADDRESS, block_number=12),
        ],
        page_key=None,
    )

    class DualStreamProvider(EthereumProvider):
        name = "dual"

        def __init__(self) -> None:
            self.calls = 0

        async def get_asset_transfers(self, **kwargs) -> ProviderPage:
            self.calls += 1
            if kwargs.get("from_address"):
                return outbound
            return inbound

    adapter = EthereumAdapter(provider=DualStreamProvider())

    import asyncio

    result = asyncio.get_event_loop().run_until_complete(
        adapter.fetch_transfers(TransferQuery(address=VALID_ADDRESS, direction=TransferDirection.BOTH))
    )
    hashes = [t.transaction_hash for t in result.transactions]
    assert hashes.count("0xshared") == 1
    assert len(result.transactions) == 3
    assert result.status in (BlockchainErrorCode.SUCCESS, BlockchainErrorCode.PARTIAL_SUCCESS)


def test_max_transfers_bound():
    transfers = [make_transfer(f"0x{i}", "1", block_number=i) for i in range(10)]
    pages = [
        ProviderPage(provider="sequence", transfers=transfers[:5], page_key="1"),
        ProviderPage(provider="sequence", transfers=transfers[5:], page_key=None),
    ]
    provider = SequenceProvider(pages)
    adapter = EthereumAdapter(provider=provider)

    import asyncio

    result = asyncio.get_event_loop().run_until_complete(
        adapter.fetch_transfers(
            TransferQuery(
                address=VALID_ADDRESS,
                direction=TransferDirection.OUTBOUND,
                max_transfers=3,
                page_size=5,
            )
        )
    )
    assert len(result.transactions) == 3
    assert result.has_more is True
