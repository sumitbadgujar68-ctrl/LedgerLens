import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

import httpx

from app.services.blockchain.canonical import TransferCategory
from app.services.blockchain.errors import (
    InvalidInputError,
    ProviderResponseError,
    ProviderUnavailableError,
    RateLimitError,
)
from app.services.blockchain.providers.base import EthereumProvider, ProviderPage, ProviderTransfer

logger = logging.getLogger("ledgerlens.blockchain.alchemy")

_CATEGORY_TO_ALCHEMY = {
    TransferCategory.EXTERNAL: "external",
    TransferCategory.INTERNAL: "internal",
    TransferCategory.ERC20: "erc20",
    TransferCategory.ERC721: "erc721",
    TransferCategory.ERC1155: "erc1155",
    TransferCategory.SPECIALNFT: "specialnft",
}

_ALCHEMY_TO_CATEGORY = {v: k for k, v in _CATEGORY_TO_ALCHEMY.items()}
_ALCHEMY_TO_CATEGORY["specialnft"] = TransferCategory.SPECIALNFT


def _hex_to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text, 16) if text.lower().startswith("0x") else int(text)
        except ValueError:
            return None
    return None


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class AlchemyProvider(EthereumProvider):
    name = "alchemy"

    def __init__(
        self,
        api_key: str,
        network: str = "eth-mainnet",
        timeout_seconds: float = 30.0,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        if not api_key:
            raise InvalidInputError("Alchemy API key is required", provider=self.name)
        self._api_key = api_key
        self._network = network
        self._endpoint = f"https://{network}.g.alchemy.com/v2/{api_key}"
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=timeout_seconds)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    def _sanitize(self, message: str) -> str:
        if self._api_key and self._api_key in message:
            return message.replace(self._api_key, "***")
        return message

    async def get_asset_transfers(
        self,
        *,
        from_address: Optional[str] = None,
        to_address: Optional[str] = None,
        categories: Optional[List[TransferCategory]] = None,
        from_block: str = "0x0",
        to_block: str = "latest",
        page_key: Optional[str] = None,
        max_count: int = 100,
        with_metadata: bool = True,
        exclude_zero_value: bool = False,
    ) -> ProviderPage:
        if not from_address and not to_address:
            raise InvalidInputError(
                "from_address or to_address is required",
                provider=self.name,
            )

        category_list = categories or [
            TransferCategory.EXTERNAL,
            TransferCategory.INTERNAL,
            TransferCategory.ERC20,
            TransferCategory.ERC721,
            TransferCategory.ERC1155,
        ]
        alchemy_categories = [_CATEGORY_TO_ALCHEMY[c] for c in category_list]

        params: Dict[str, Any] = {
            "fromBlock": from_block,
            "toBlock": to_block,
            "category": alchemy_categories,
            "excludeZeroValue": exclude_zero_value,
            "withMetadata": with_metadata,
            "maxCount": hex(max_count),
        }
        if from_address:
            params["fromAddress"] = from_address
        if to_address:
            params["toAddress"] = to_address
        if page_key:
            params["pageKey"] = page_key

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "alchemy_getAssetTransfers",
            "params": [params],
        }

        try:
            response = await self._client.post(self._endpoint, json=payload)
        except httpx.TimeoutException as exc:
            raise ProviderUnavailableError(
                self._sanitize(f"Alchemy request timed out: {exc}"),
                provider=self.name,
            ) from None
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(
                self._sanitize(f"Alchemy connection failed: {exc}"),
                provider=self.name,
            ) from None

        if response.status_code == 429:
            raise RateLimitError("Alchemy rate limit exceeded (HTTP 429)", provider=self.name)
        if response.status_code >= 500:
            raise ProviderUnavailableError(
                self._sanitize(
                    f"Alchemy server error (HTTP {response.status_code}): {response.text[:500]}"
                ),
                provider=self.name,
            )
        if response.status_code >= 400:
            raise ProviderResponseError(
                self._sanitize(f"Alchemy request failed (HTTP {response.status_code}): {response.text[:500]}"),
                provider=self.name,
            )

        try:
            body = response.json()
        except json.JSONDecodeError:
            raise ProviderResponseError("Alchemy returned invalid JSON", provider=self.name) from None

        if not isinstance(body, dict):
            raise ProviderResponseError("Alchemy returned unexpected JSON shape", provider=self.name)

        if "error" in body and body["error"] is not None:
            error = body["error"]
            error_text = json.dumps(error) if not isinstance(error, str) else error
            error_text = self._sanitize(error_text)
            lowered = error_text.lower()
            if "rate limit" in lowered or "too many" in lowered:
                raise RateLimitError(error_text, provider=self.name)
            raise ProviderResponseError(error_text, provider=self.name)

        result = body.get("result")
        if not isinstance(result, dict):
            raise ProviderResponseError("Alchemy result missing or invalid", provider=self.name)

        raw_transfers = result.get("transfers")
        if raw_transfers is None:
            raw_transfers = []
        if not isinstance(raw_transfers, list):
            raise ProviderResponseError("Alchemy transfers field is not a list", provider=self.name)

        transfers = [self._parse_transfer(item) for item in raw_transfers]
        next_page_key = result.get("pageKey")
        if next_page_key is not None and not isinstance(next_page_key, str):
            next_page_key = str(next_page_key)
        if next_page_key == "":
            next_page_key = None

        return ProviderPage(provider=self.name, transfers=transfers, page_key=next_page_key)

    def _parse_transfer(self, item: Any) -> ProviderTransfer:
        if not isinstance(item, dict):
            raise ProviderResponseError("Alchemy transfer entry is not an object", provider=self.name)

        tx_hash = item.get("hash")
        from_address = item.get("from")
        provider_reference = item.get("uniqueId") or tx_hash
        if not tx_hash or not from_address or not provider_reference:
            raise ProviderResponseError(
                "Alchemy transfer missing required fields (hash/from/uniqueId)",
                provider=self.name,
            )

        raw_contract = item.get("rawContract") or {}
        if not isinstance(raw_contract, dict):
            raw_contract = {}

        category_raw = str(item.get("category") or "unknown").lower()
        category = _ALCHEMY_TO_CATEGORY.get(category_raw, TransferCategory.UNKNOWN)

        amount_raw = self._extract_amount_raw(item, raw_contract, category)
        decimals = self._extract_decimals(raw_contract, category)

        metadata = item.get("metadata") or {}
        block_timestamp = None
        if isinstance(metadata, dict):
            block_timestamp = _parse_timestamp(metadata.get("blockTimestamp"))

        token_contract = raw_contract.get("address") or item.get("tokenContract")
        if isinstance(token_contract, dict):
            token_contract = token_contract.get("address")

        token_id = item.get("erc721TokenId") or item.get("tokenId")
        if token_id is not None:
            token_id = str(token_id)

        return ProviderTransfer(
            provider=self.name,
            chain="ethereum",
            transaction_hash=str(tx_hash),
            block_number=_hex_to_int(item.get("blockNum")),
            block_timestamp=block_timestamp,
            from_address=str(from_address),
            to_address=str(item["to"]) if item.get("to") is not None else None,
            asset_symbol=item.get("asset"),
            token_contract=str(token_contract) if token_contract else None,
            amount_raw=amount_raw,
            decimals=decimals,
            transfer_category=category,
            token_id=token_id,
            provider_reference=str(provider_reference),
            raw_reference=str(item.get("blockNum") or "") or None,
            raw=dict(item),
        )

    @staticmethod
    def _extract_amount_raw(item: Dict[str, Any], raw_contract: Dict[str, Any], category: TransferCategory) -> Optional[str]:
        hex_value = raw_contract.get("value")
        if isinstance(hex_value, str) and hex_value:
            try:
                return str(int(hex_value, 16))
            except ValueError:
                pass
        elif isinstance(hex_value, int):
            return str(hex_value)

        value = item.get("value")
        if value is None:
            return None
        if isinstance(value, int):
            decimals = AlchemyProvider._extract_decimals(raw_contract, category)
            return str(value * (10 ** decimals if decimals else 1))
        if isinstance(value, str):
            try:
                from decimal import Decimal

                d = Decimal(value)
                decimals = AlchemyProvider._extract_decimals(raw_contract, category)
                scaled = d * (Decimal(10) ** decimals if decimals else Decimal(1))
                if scaled == scaled.to_integral_value():
                    return str(int(scaled))
                return str(scaled)
            except Exception:
                return None
        if isinstance(value, float):
            from decimal import Decimal

            decimals = AlchemyProvider._extract_decimals(raw_contract, category)
            scaled = Decimal(str(value)) * (Decimal(10) ** decimals if decimals else Decimal(1))
            if scaled == scaled.to_integral_value():
                return str(int(scaled))
            return str(scaled)
        return None

    @staticmethod
    def _extract_decimals(raw_contract: Dict[str, Any], category: TransferCategory) -> int:
        hex_decimals = raw_contract.get("decimal")
        if isinstance(hex_decimals, str) and hex_decimals:
            try:
                return int(hex_decimals, 16)
            except ValueError:
                pass
        elif isinstance(hex_decimals, int):
            return hex_decimals

        if category == TransferCategory.EXTERNAL:
            return 18
        if category == TransferCategory.INTERNAL:
            return 18
        if category in (TransferCategory.ERC721,):
            return 0
        return 18
