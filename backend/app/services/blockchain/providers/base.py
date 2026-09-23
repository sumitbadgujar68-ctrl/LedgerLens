from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.services.blockchain.canonical import TransferCategory


class ProviderTransfer(BaseModel):
    provider: str
    chain: str = "ethereum"
    transaction_hash: str
    block_number: Optional[int] = None
    block_timestamp: Optional[datetime] = None
    from_address: str
    to_address: Optional[str] = None
    asset_symbol: Optional[str] = None
    token_contract: Optional[str] = None
    amount_raw: Optional[str] = None
    decimals: Optional[int] = None
    transfer_category: TransferCategory = TransferCategory.UNKNOWN
    token_id: Optional[str] = None
    provider_reference: str
    status_hint: Optional[str] = None
    raw_reference: Optional[str] = None
    raw: dict = Field(default_factory=dict)


class ProviderPage(BaseModel):
    provider: str
    transfers: List[ProviderTransfer] = Field(default_factory=list)
    page_key: Optional[str] = None


class EthereumProvider(ABC):
    name: str

    @abstractmethod
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
        raise NotImplementedError
