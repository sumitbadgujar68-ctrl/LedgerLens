from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.services.blockchain.errors import BlockchainErrorCode


class AssetType(str, Enum):
    NATIVE = "native"
    ERC20 = "erc20"
    ERC721 = "erc721"
    ERC1155 = "erc1155"
    UNKNOWN = "unknown"


class TransferCategory(str, Enum):
    EXTERNAL = "external"
    INTERNAL = "internal"
    ERC20 = "erc20"
    ERC721 = "erc721"
    ERC1155 = "erc1155"
    SPECIALNFT = "specialnft"
    UNKNOWN = "unknown"


class TransactionType(str, Enum):
    TRANSFER = "transfer"
    CONTRACT_INTERACTION = "contract_interaction"
    UNKNOWN = "unknown"


class TransactionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    UNKNOWN = "unknown"


class TransferDirection(str, Enum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"
    BOTH = "both"


class CanonicalTransaction(BaseModel):
    chain: str = "ethereum"
    transaction_hash: str
    block_number: Optional[int] = None
    block_timestamp: Optional[datetime] = None
    from_address: str
    to_address: Optional[str] = None
    asset: Optional[str] = None
    asset_type: AssetType = AssetType.UNKNOWN
    amount: Decimal = Decimal("0")
    decimals: int = 0
    token_contract: Optional[str] = None
    transfer_category: TransferCategory = TransferCategory.UNKNOWN
    transaction_type: TransactionType = TransactionType.TRANSFER
    status: TransactionStatus = TransactionStatus.UNKNOWN
    gas_used: Optional[int] = None
    max_fee_per_gas: Optional[Decimal] = None
    priority_fee_per_gas: Optional[Decimal] = None
    total_fee: Optional[Decimal] = None
    provider: str
    provider_reference: str
    raw_reference: Optional[str] = None


class TransferQuery(BaseModel):
    address: str
    direction: TransferDirection = TransferDirection.BOTH
    categories: List[TransferCategory] = Field(
        default_factory=lambda: [
            TransferCategory.EXTERNAL,
            TransferCategory.INTERNAL,
            TransferCategory.ERC20,
            TransferCategory.ERC721,
            TransferCategory.ERC1155,
        ]
    )
    from_block: str = "0x0"
    to_block: str = "latest"
    max_pages: int = Field(default=10, ge=1, le=100)
    max_transfers: int = Field(default=1000, ge=1, le=10000)
    page_size: int = Field(default=100, ge=1, le=1000)
    with_metadata: bool = True
    exclude_zero_value: bool = False


class TransferFetchResult(BaseModel):
    status: BlockchainErrorCode
    transactions: List[CanonicalTransaction] = Field(default_factory=list)
    provider: str
    page_count: int = 0
    has_more: bool = False
    errors: List[str] = Field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return self.status in (
            BlockchainErrorCode.SUCCESS,
            BlockchainErrorCode.PARTIAL_SUCCESS,
            BlockchainErrorCode.NO_DATA,
        )
