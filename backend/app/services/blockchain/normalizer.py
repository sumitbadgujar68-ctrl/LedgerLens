import json
from decimal import Decimal, InvalidOperation
from typing import Optional

from app.services.blockchain.canonical import (
    AssetType,
    CanonicalTransaction,
    TransactionStatus,
    TransactionType,
    TransferCategory,
)
from app.services.blockchain.providers.base import ProviderTransfer

_CATEGORY_TO_ASSET_TYPE = {
    TransferCategory.EXTERNAL: AssetType.NATIVE,
    TransferCategory.INTERNAL: AssetType.NATIVE,
    TransferCategory.ERC20: AssetType.ERC20,
    TransferCategory.ERC721: AssetType.ERC721,
    TransferCategory.ERC1155: AssetType.ERC1155,
    TransferCategory.SPECIALNFT: AssetType.ERC721,
    TransferCategory.UNKNOWN: AssetType.UNKNOWN,
}


def normalize_address(address: Optional[str]) -> Optional[str]:
    if address is None:
        return None
    return address.strip().lower()


class TransactionNormalizer:
    def normalize(self, transfer: ProviderTransfer) -> CanonicalTransaction:
        decimals = transfer.decimals if transfer.decimals is not None else 18
        amount = self._to_decimal(transfer.amount_raw, decimals)
        asset_type = _CATEGORY_TO_ASSET_TYPE.get(transfer.transfer_category, AssetType.UNKNOWN)
        status = self._to_status(transfer.status_hint)
        raw_reference = transfer.raw_reference
        if raw_reference is None and transfer.raw:
            try:
                raw_reference = json.dumps(transfer.raw, default=str, separators=(",", ":"))[:1000]
            except (TypeError, ValueError):
                raw_reference = transfer.provider_reference

        return CanonicalTransaction(
            chain=transfer.chain,
            transaction_hash=transfer.transaction_hash,
            block_number=transfer.block_number,
            block_timestamp=transfer.block_timestamp,
            from_address=normalize_address(transfer.from_address) or "",
            to_address=normalize_address(transfer.to_address),
            asset=transfer.asset_symbol,
            asset_type=asset_type,
            amount=amount,
            decimals=decimals,
            token_contract=normalize_address(transfer.token_contract),
            transfer_category=transfer.transfer_category,
            transaction_type=TransactionType.TRANSFER,
            status=status,
            provider=transfer.provider,
            provider_reference=transfer.provider_reference,
            raw_reference=raw_reference,
        )

    @staticmethod
    def _to_decimal(amount_raw: Optional[str], decimals: int) -> Decimal:
        if amount_raw is None or amount_raw == "":
            return Decimal("0")
        try:
            base = Decimal(amount_raw)
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"Invalid amount_raw: {amount_raw}") from exc
        if decimals <= 0:
            return base
        return base / (Decimal(10) ** decimals)

    @staticmethod
    def _to_status(status_hint: Optional[str]) -> TransactionStatus:
        if not status_hint:
            return TransactionStatus.UNKNOWN
        hint = status_hint.strip().lower()
        mapping = {
            "success": TransactionStatus.SUCCESS,
            "1": TransactionStatus.SUCCESS,
            "failed": TransactionStatus.FAILED,
            "0": TransactionStatus.FAILED,
            "pending": TransactionStatus.PENDING,
        }
        return mapping.get(hint, TransactionStatus.UNKNOWN)
