import logging
import re
from abc import ABC, abstractmethod
from typing import Optional

from app.services.blockchain.canonical import (
    TransferDirection,
    TransferFetchResult,
    TransferQuery,
)
from app.services.blockchain.errors import (
    BlockchainError,
    BlockchainErrorCode,
    InvalidInputError,
    ProviderResponseError,
    RateLimitError,
    ProviderUnavailableError,
)
from app.services.blockchain.normalizer import TransactionNormalizer, normalize_address
from app.services.blockchain.providers.base import EthereumProvider, ProviderTransfer

logger = logging.getLogger("ledgerlens.blockchain.adapter")

_ETH_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


def is_valid_ethereum_address(address: str) -> bool:
    return bool(address) and bool(_ETH_ADDRESS_RE.match(address.strip()))


class BlockchainAdapter(ABC):
    @abstractmethod
    async def fetch_transfers(self, query: TransferQuery) -> TransferFetchResult:
        raise NotImplementedError

    @abstractmethod
    def validate_address(self, address: str) -> str:
        raise NotImplementedError


class EthereumAdapter(BlockchainAdapter):
    def __init__(
        self,
        provider: EthereumProvider,
        normalizer: Optional[TransactionNormalizer] = None,
    ) -> None:
        self._provider = provider
        self._normalizer = normalizer or TransactionNormalizer()

    @property
    def provider_name(self) -> str:
        return self._provider.name

    def validate_address(self, address: str) -> str:
        cleaned = (address or "").strip()
        if not is_valid_ethereum_address(cleaned):
            raise InvalidInputError(
                "Invalid Ethereum address (expected 0x + 40 hex characters)",
                provider=self.provider_name,
            )
        return cleaned.lower()


    async def fetch_transfers(self, query: TransferQuery) -> TransferFetchResult:
        provider = self.provider_name
        try:
            address = self.validate_address(query.address)
        except InvalidInputError as exc:
            return TransferFetchResult(
                status=BlockchainErrorCode.INVALID_INPUT,
                transactions=[],
                provider=provider,
                errors=[exc.message],
            )

        if query.direction == TransferDirection.BOTH:
            outbound = await self._fetch_stream(address, query, outbound=True)
            inbound = await self._fetch_stream(address, query, outbound=False)
            return self._merge_results(outbound, inbound, query)

        outbound = query.direction == TransferDirection.OUTBOUND
        return await self._fetch_stream(address, query, outbound=outbound)

    async def _fetch_stream(
        self,
        address: str,
        query: TransferQuery,
        *,
        outbound: bool,
    ) -> TransferFetchResult:
        provider = self.provider_name
        transactions = []
        errors = []
        page_count = 0
        page_key: Optional[str] = None
        has_more = False
        hit_error_code: Optional[BlockchainErrorCode] = None

        from_address = address if outbound else None
        to_address = None if outbound else address

        try:
            while page_count < query.max_pages and len(transactions) < query.max_transfers:
                remaining = query.max_transfers - len(transactions)
                max_count = min(query.page_size, remaining)
                if max_count <= 0:
                    break

                page = await self._provider.get_asset_transfers(
                    from_address=from_address,
                    to_address=to_address,
                    categories=query.categories,
                    from_block=query.from_block,
                    to_block=query.to_block,
                    page_key=page_key,
                    max_count=max_count,
                    with_metadata=query.with_metadata,
                    exclude_zero_value=query.exclude_zero_value,
                )
                page_count += 1

                for raw_transfer in page.transfers:
                    if len(transactions) >= query.max_transfers:
                        has_more = True
                        break
                    try:
                        canonical = self._normalizer.normalize(raw_transfer)
                        transactions.append(canonical)
                    except (ValueError, ProviderResponseError) as exc:
                        errors.append(f"normalization_failed: {exc}")

                page_key = page.page_key
                if page_key:
                    has_more = True
                else:
                    has_more = False
                    break

                if len(transactions) >= query.max_transfers:
                    has_more = True
                    break

            if page_count >= query.max_pages and page_key:
                has_more = True
                errors.append(f"page_limit_reached: max_pages={query.max_pages}")

        except RateLimitError as exc:
            hit_error_code = BlockchainErrorCode.RATE_LIMITED
            errors.append(exc.message)
        except ProviderUnavailableError as exc:
            hit_error_code = BlockchainErrorCode.PROVIDER_UNAVAILABLE
            errors.append(exc.message)
        except InvalidInputError as exc:
            hit_error_code = BlockchainErrorCode.INVALID_INPUT
            errors.append(exc.message)
        except ProviderResponseError as exc:
            hit_error_code = BlockchainErrorCode.FAILED
            errors.append(exc.message)
        except BlockchainError as exc:
            hit_error_code = exc.code
            errors.append(exc.message)
        except Exception as exc:  # noqa: BLE001 - surface unexpected provider failures explicitly
            hit_error_code = BlockchainErrorCode.FAILED
            errors.append(f"unexpected_error: {exc}")
            logger.exception(
                "unexpected provider failure provider=%s pages=%s", provider, page_count
            )

        if hit_error_code is not None:
            if transactions:
                status = BlockchainErrorCode.PARTIAL_SUCCESS
            else:
                status = hit_error_code
        elif errors and transactions:
            status = BlockchainErrorCode.PARTIAL_SUCCESS
        elif errors and not transactions:
            status = BlockchainErrorCode.FAILED
        elif not transactions:
            status = BlockchainErrorCode.NO_DATA
        else:
            status = BlockchainErrorCode.SUCCESS

        return TransferFetchResult(
            status=status,
            transactions=transactions,
            provider=provider,
            page_count=page_count,
            has_more=has_more,
            errors=errors,
        )

    def _merge_results(
        self,
        outbound: TransferFetchResult,
        inbound: TransferFetchResult,
        query: TransferQuery,
    ) -> TransferFetchResult:
        seen = set()
        merged = []
        for tx in list(outbound.transactions) + list(inbound.transactions):
            key = (tx.transaction_hash, tx.from_address, tx.to_address, tx.provider_reference)
            if key in seen:
                continue
            seen.add(key)
            merged.append(tx)

        merged.sort(
            key=lambda t: (
                t.block_number if t.block_number is not None else -1,
                t.transaction_hash,
                t.provider_reference,
            )
        )
        if len(merged) > query.max_transfers:
            merged = merged[: query.max_transfers]

        errors = list(dict.fromkeys(outbound.errors + inbound.errors))
        statuses = {outbound.status, inbound.status}
        if BlockchainErrorCode.PARTIAL_SUCCESS in statuses:
            status = BlockchainErrorCode.PARTIAL_SUCCESS
        elif BlockchainErrorCode.FAILED in statuses and statuses & {
            BlockchainErrorCode.SUCCESS,
            BlockchainErrorCode.NO_DATA,
            BlockchainErrorCode.RATE_LIMITED,
            BlockchainErrorCode.PROVIDER_UNAVAILABLE,
            BlockchainErrorCode.INVALID_INPUT,
        }:
            status = BlockchainErrorCode.PARTIAL_SUCCESS
        elif statuses == {BlockchainErrorCode.NO_DATA}:
            status = BlockchainErrorCode.NO_DATA
        elif len(statuses) == 1:
            status = next(iter(statuses))
        elif BlockchainErrorCode.SUCCESS in statuses:
            status = BlockchainErrorCode.PARTIAL_SUCCESS
        else:
            status = BlockchainErrorCode.FAILED if not merged else BlockchainErrorCode.PARTIAL_SUCCESS

        if not errors and not merged and status == BlockchainErrorCode.FAILED:
            status = BlockchainErrorCode.NO_DATA

        return TransferFetchResult(
            status=status,
            transactions=merged,
            provider=outbound.provider or inbound.provider,
            page_count=outbound.page_count + inbound.page_count,
            has_more=outbound.has_more or inbound.has_more,
            errors=errors,
        )

_BTC_ADDRESS_RE = re.compile(r"^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}$")
_TRON_ADDRESS_RE = re.compile(r"^T[a-zA-HJ-NP-Z0-9]{33}$")

def is_valid_bitcoin_address(address: str) -> bool:
    return bool(address) and bool(_BTC_ADDRESS_RE.match(address.strip()))

def is_valid_tron_address(address: str) -> bool:
    return bool(address) and bool(_TRON_ADDRESS_RE.match(address.strip()))

class BitcoinAdapter(EthereumAdapter):
    def validate_address(self, address: str) -> str:
        cleaned = (address or "").strip()
        if not is_valid_bitcoin_address(cleaned):
            raise InvalidInputError(
                "Invalid Bitcoin address",
                provider=self.provider_name,
            )
        return cleaned

class TronAdapter(EthereumAdapter):
    def validate_address(self, address: str) -> str:
        cleaned = (address or "").strip()
        if not is_valid_tron_address(cleaned):
            raise InvalidInputError(
                "Invalid Tron address",
                provider=self.provider_name,
            )
        return cleaned
