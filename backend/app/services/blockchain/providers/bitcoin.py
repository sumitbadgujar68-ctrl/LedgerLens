import httpx
from datetime import datetime, timezone
from typing import List, Optional

from app.services.blockchain.canonical import TransferCategory
from app.services.blockchain.errors import ProviderResponseError, RateLimitError
from app.services.blockchain.providers.base import EthereumProvider, ProviderPage, ProviderTransfer

class BlockstreamBitcoinProvider(EthereumProvider):
    name = "blockstream_bitcoin"

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
        # We query blockstream.info API: /api/address/{address}/txs
        # Pagination in blockstream uses the last txid seen (page_key)
        
        target_address = from_address or to_address
        if not target_address:
            raise ProviderResponseError("Must specify either from_address or to_address for Bitcoin", provider=self.name)
            
        base_url = f"https://blockstream.info/api/address/{target_address}/txs"
        if page_key:
            base_url = f"https://blockstream.info/api/address/{target_address}/txs/chain/{page_key}"
            
        async with httpx.AsyncClient() as client:
            resp = await client.get(base_url, timeout=10.0)
            if resp.status_code == 429:
                raise RateLimitError("Rate limited by Blockstream API", provider=self.name)
            if resp.status_code != 200:
                raise ProviderResponseError(f"Blockstream API returned {resp.status_code}", provider=self.name)
                
            txs = resp.json()
            
        transfers = []
        next_page_key = None
        
        for tx in txs:
            tx_hash = tx.get("txid", "")
            block_height = tx.get("status", {}).get("block_height")
            block_time = tx.get("status", {}).get("block_time")
            dt = datetime.fromtimestamp(block_time, tz=timezone.utc) if block_time else None
            
            if from_address:
                # Is from_address in inputs?
                is_sender = any(
                    (vin.get("prevout") or {}).get("scriptpubkey_address") == from_address 
                    for vin in tx.get("vin", [])
                )
                if is_sender:
                    for vout in tx.get("vout", []):
                        out_addr = vout.get("scriptpubkey_address")
                        if out_addr and out_addr != from_address:
                            transfers.append(ProviderTransfer(
                                provider=self.name,
                                chain="bitcoin",
                                transaction_hash=tx_hash,
                                block_number=block_height,
                                block_timestamp=dt,
                                from_address=from_address,
                                to_address=out_addr,
                                asset_symbol="BTC",
                                amount_raw=hex(vout.get("value", 0)),
                                decimals=8,
                                provider_reference=tx_hash,
                                raw=tx
                            ))
            elif to_address:
                # Is to_address in outputs?
                is_receiver = any(
                    vout.get("scriptpubkey_address") == to_address 
                    for vout in tx.get("vout", [])
                )
                if is_receiver:
                    for vin in tx.get("vin", []):
                        in_addr = (vin.get("prevout") or {}).get("scriptpubkey_address")
                        if in_addr and in_addr != to_address:
                            transfers.append(ProviderTransfer(
                                provider=self.name,
                                chain="bitcoin",
                                transaction_hash=tx_hash,
                                block_number=block_height,
                                block_timestamp=dt,
                                from_address=in_addr,
                                to_address=to_address,
                                asset_symbol="BTC",
                                amount_raw=hex((vin.get("prevout") or {}).get("value", 0)),
                                decimals=8,
                                provider_reference=tx_hash,
                                raw=tx
                            ))
            if len(transfers) >= max_count:
                break

        # Fallback: if from_address was specified but has no outbound transfers (e.g. deposit wallet that only received BTC),
        # extract inbound funding transfers so the investigator receives real on-chain transaction provenance.
        if from_address and not transfers:
            for tx in txs:
                tx_hash = tx.get("txid", "")
                block_height = tx.get("status", {}).get("block_height")
                block_time = tx.get("status", {}).get("block_time")
                dt = datetime.fromtimestamp(block_time, tz=timezone.utc) if block_time else None
                is_receiver = any(
                    vout.get("scriptpubkey_address") == from_address 
                    for vout in tx.get("vout", [])
                )
                if is_receiver:
                    for vin in tx.get("vin", []):
                        in_addr = (vin.get("prevout") or {}).get("scriptpubkey_address")
                        if in_addr and in_addr != from_address:
                            transfers.append(ProviderTransfer(
                                provider=self.name,
                                chain="bitcoin",
                                transaction_hash=tx_hash,
                                block_number=block_height,
                                block_timestamp=dt,
                                from_address=in_addr,
                                to_address=from_address,
                                asset_symbol="BTC",
                                amount_raw=hex((vin.get("prevout") or {}).get("value", 0)),
                                decimals=8,
                                provider_reference=tx_hash,
                                raw=tx
                            ))
                if len(transfers) >= max_count:
                    break

        # Only paginate if we haven't found enough transfers yet and there's a full page
        if len(transfers) < max_count and len(txs) == 25:
            next_page_key = txs[-1].get("txid")
            
        return ProviderPage(
            provider=self.name,
            transfers=transfers,
            page_key=next_page_key
        )
