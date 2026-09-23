from enum import Enum
from typing import Any, Dict, Optional


class BlockchainErrorCode(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    NO_DATA = "NO_DATA"
    RATE_LIMITED = "RATE_LIMITED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    INVALID_INPUT = "INVALID_INPUT"


class BlockchainError(Exception):
    def __init__(
        self,
        code: BlockchainErrorCode,
        message: str,
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.code = code
        self.message = message
        self.provider = provider
        self.details = details or {}
        super().__init__(f"[{code.value}] {message}")


class InvalidInputError(BlockchainError):
    def __init__(self, message: str, provider: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(BlockchainErrorCode.INVALID_INPUT, message, provider, details)


class RateLimitError(BlockchainError):
    def __init__(self, message: str, provider: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(BlockchainErrorCode.RATE_LIMITED, message, provider, details)


class ProviderUnavailableError(BlockchainError):
    def __init__(self, message: str, provider: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(BlockchainErrorCode.PROVIDER_UNAVAILABLE, message, provider, details)


class ProviderResponseError(BlockchainError):
    def __init__(self, message: str, provider: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(BlockchainErrorCode.FAILED, message, provider, details)
