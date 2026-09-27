import httpx
from datetime import datetime, timezone
from typing import List, Optional

from app.services.blockchain.canonical import TransferCategory
from app.services.blockchain.errors import ProviderResponseError, RateLimitError
from app.services.blockchain.providers.base import EthereumProvider, ProviderPage, ProviderTransfer

class TronGridProvider(EthereumProvider):
    name = "trongrid"

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
        target_address = from_address or to_address
        if not target_address:
            raise ProviderResponseError("Must specify either from_address or to_address for Tron", provider=self.name)
            
        # We query TronGrid TRC20 transfers which are the most common in forensics (USDT).
        base_url = f"https://api.trongrid.io/v1/accounts/{target_address}/transactions/trc20"
        
        params = {"limit": min(max_count, 200)}
        if page_key:
            params["fingerprint"] = page_key
            
        async with httpx.AsyncClient() as client:
            resp = await client.get(base_url, params=params, timeout=10.0)
            if resp.status_code == 429:
                raise RateLimitError("Rate limited by TronGrid API", provider=self.name)
            if resp.status_code != 200:
                raise ProviderResponseError(f"TronGrid API returned {resp.status_code}", provider=self.name)
                
            data = resp.json()
            if not data.get("success", False):
                raise ProviderResponseError("TronGrid API returned success=false", provider=self.name)
                
            txs = data.get("data", [])
            
        transfers = []
        next_page_key = data.get("meta", {}).get("fingerprint")
        
        for tx in txs:
            tx_hash = tx.get("transaction_id")
            block_timestamp = tx.get("block_timestamp")
            dt = datetime.fromtimestamp(block_timestamp / 1000.0, tz=timezone.utc) if block_timestamp else None
            
            # Identify if it matches our direction
            tx_from = tx.get("from")
            tx_to = tx.get("to")
            
            if from_address and tx_from != from_address:
                continue
            if to_address and tx_to != to_address:
                continue
                
            val_str = tx.get("value", "0")
            
            transfers.append(ProviderTransfer(
                provider=self.name,
                chain="tron",
                transaction_hash=tx_hash,
                block_timestamp=dt,
                from_address=tx_from,
                to_address=tx_to,
                asset_symbol=tx.get("token_info", {}).get("symbol", "TRC20"),
                token_contract=tx.get("token_info", {}).get("address"),
                amount_raw=hex(int(val_str)) if val_str.isdigit() else "0x0",
                decimals=int(tx.get("token_info", {}).get("decimals", 6)),
                provider_reference=tx_hash,
                raw=tx
            ))
            
        return ProviderPage(
            provider=self.name,
            transfers=transfers,
            page_key=next_page_key
        )
