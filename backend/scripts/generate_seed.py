import json
import os

with open('scripts/seed_demo_data.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
'''def build_adapter():
    from app.config import settings

    api_key = settings.alchemy_api_key
    if not api_key:
        raise RuntimeError("ALCHEMY_API_KEY is not configured; cannot run live traces")
    return EthereumAdapter(provider=AlchemyProvider(api_key=api_key, network=settings.alchemy_network))''',
'''def build_adapters():
    from app.config import settings
    from app.services.blockchain import AlchemyProvider, EthereumAdapter
    from app.services.blockchain.adapter import BitcoinAdapter, TronAdapter

    api_key = settings.alchemy_api_key
    if not api_key:
        raise RuntimeError("ALCHEMY_API_KEY is not configured; cannot run live traces")
    return {
        "ethereum": EthereumAdapter(provider=AlchemyProvider(api_key=api_key, network=settings.alchemy_network)),
        "bitcoin": BitcoinAdapter(provider=AlchemyProvider(api_key=api_key, network="btc-mainnet")),
        "tron": TronAdapter(provider=AlchemyProvider(api_key=api_key, network="tron-mainnet")),
    }'''
)
content = content.replace('service = TraceService(build_adapter())', 'service = TraceService(build_adapters())')

content = content.replace(
'''    if skip_live:
        log(f"{spec['case_number']}: --skip-live, no trace run")
        return None''',
'''    if skip_live:
        log(f"{spec['case_number']}: --skip-live, mocking trace and graph")
        trace = TraceRun(
            trace_id=uuid.uuid4(),
            case_id=case.case_id,
            start_wallet_address=spec["wallet"].lower(),
            blockchain=spec.get("blockchain", "ethereum"),
            direction=spec.get("direction", "outbound"),
            max_hops=1,
            max_branches=2,
            min_amount=None,
            asset_filters=[],
            time_range_start=None,
            time_range_end=None,
            status="completed",
            result_status="success",
            provider="demo_mock",
            summary={"wallet_count": 3, "transaction_count": 2, "edge_count": 2},
            parameters={},
            errors=[]
        )
        db.add(trace)
        
        graph_payload = {
            "root_wallet_address": spec["wallet"].lower(),
            "blockchain": spec.get("blockchain", "ethereum"),
            "node_count": 3,
            "edge_count": 2,
            "max_hop_depth": 1,
            "nodes": [
                {"id": spec["wallet"].lower(), "type": "wallet", "hop": 0, "metadata": {"root": True}},
                {"id": _demo_address("de10"), "type": "wallet", "hop": 1, "metadata": {}},
                {"id": _demo_address("de11"), "type": "wallet", "hop": 1, "metadata": {}}
            ],
            "edges": [
                {"id": "mockedge1", "source": spec["wallet"].lower(), "target": _demo_address("de10"), "type": "transferred_to", "transaction_hash": "0xabc", "amount": "100000", "hop": 1},
                {"id": "mockedge2", "source": spec["wallet"].lower(), "target": _demo_address("de11"), "type": "transferred_to", "transaction_hash": "0xdef", "amount": "50000", "hop": 1}
            ]
        }
        db.add(
            GraphRecord(
                case_id=case.case_id,
                trace_id=trace.trace_id,
                root_wallet_address=spec["wallet"].lower(),
                blockchain=spec.get("blockchain", "ethereum"),
                max_hop_depth=1,
                branch_limit=2,
                dust_threshold=None,
                time_window_start=None,
                time_window_end=None,
                node_count=3,
                edge_count=2,
                graph_data=graph_payload,
            )
        )
        
        await db.flush()
        return trace'''
)

demo_cases_start = content.find('DEMO_CASES: List[Dict[str, Any]] = [')
demo_cases_end = content.find(']', demo_cases_start) + 1

eth_wallets = [
    '0xf30ba13e4b04Ce5dC4D254Ae5FA95477800F0EB0',
    '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
    '0xBD612a3f30dcA67bF60a39Fd0D35e39B7aB80774',
    '0x28C6c06298d514Db089934071355E22Af164fC78',
    '0x00000000219ab540356cBB839Cbe05303d7705Fa',
    '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
    '0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8',
    '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
    '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
    '0x1111111254fb6c44bac0bed2854e76f90643097d'
]
btc_wallets = [
    'bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv24sq90ecnvqqjwvw97',
    '34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo',
    '1P5ZEDWTKTFGxQjZphgWPQUpe554WKDfHQ',
    'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh',
    '3FHNQ5k4F4x3Y4JbMowXJd4A6K43ZKQJjQ',
    'bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4',
    '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
    '3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy',
    '1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF',
    'bc1qa5wkgaew2dkv56kfvj49j0av5nml45x9ek9hz6'
]
tron_wallets = [
    'TAUN6FwrnwwmaEqYcckffC7wYmbaS6cBiX',
    'TT2T17KZhoDu47i2E4FWxfG79zpe56sq8c',
    'TXLAQ63Xg1NDyeVStL9vYk6hL6BvX9U7wW',
    'TKW4y74kXQf89Qj73eX8Z2H3x19S111wT6',
    'TDqSQfDXYG7rB58J8w3Z9Fz49XGzR327U7',
    'TLGqKkH89VbN1G45T3E9B71C8J7B9z6wT8',
    'TSD2bH7F8Z1aY8Z3N9J3T7N9J9J3T7N9J9',
    'THY6P3F2K9M6X7T3P9J3T7N9J9J3T7N9J9',
    'TC1B4Y9X5J9A2T7P8J3T7N9J9J3T7N9J9',
    'TP8A3B2F7H6N9P1J3T7N9J9J3T7N9J9'
]

cases = []
for i, (eth, btc, tron) in enumerate(zip(eth_wallets, btc_wallets, tron_wallets)):
    cases.append({
        'case_number': f'CASE-DEMO-ETH-{i+1:03d}',
        'title': f'ETH Analysis - {eth[:8]}...',
        'wallet': eth,
        'fraud_type': 'investment_scam',
        'blockchain': 'ethereum',
        'direction': 'outbound',
        'description': f'Demo ETH case {i+1}',
        'tags': ['mvp-demo', 'ethereum'],
        'trace': {'max_hops': 1, 'max_branches': 2, 'max_pages_per_wallet': 1}
    })
    cases.append({
        'case_number': f'CASE-DEMO-BTC-{i+1:03d}',
        'title': f'BTC Analysis - {btc[:8]}...',
        'wallet': btc,
        'fraud_type': 'darknet_market',
        'blockchain': 'bitcoin',
        'direction': 'outbound',
        'description': f'Demo BTC case {i+1}',
        'tags': ['mvp-demo', 'bitcoin'],
        'trace': {'max_hops': 1, 'max_branches': 2, 'max_pages_per_wallet': 1}
    })
    cases.append({
        'case_number': f'CASE-DEMO-TRON-{i+1:03d}',
        'title': f'TRON Analysis - {tron[:8]}...',
        'wallet': tron,
        'fraud_type': 'scam',
        'blockchain': 'tron',
        'direction': 'outbound',
        'description': f'Demo TRON case {i+1}',
        'tags': ['mvp-demo', 'tron'],
        'trace': {'max_hops': 1, 'max_branches': 2, 'max_pages_per_wallet': 1}
    })

cases_str = 'DEMO_CASES: List[Dict[str, Any]] = ' + json.dumps(cases, indent=4)
content = content[:demo_cases_start] + cases_str + content[demo_cases_end:]
content = content.replace("payload = CaseCreate(\n        title=spec[\"title\"],", "payload = CaseCreate(\n        title=spec[\"title\"],\n        blockchain=spec.get('blockchain', 'ethereum'),")

with open('scripts/seed_multichain_demo.py', 'w', encoding='utf-8') as f:
    f.write(content)
