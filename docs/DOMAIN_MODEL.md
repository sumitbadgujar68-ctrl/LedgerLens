# LedgerLens Domain Model

**Last Updated:** 2026-09-22  
**Phase:** PHASE 0 — FOUNDATION  
**Status:** Initial Domain Model

---

## 1. Overview

This document defines the core domain entities, relationships, and canonical data structures for LedgerLens. The domain model represents the conceptual business logic independent of database implementation or API serialization.

---

## 2. Core Domain Entities

### 2.1 Case

**Description:**  
Represents an investigation case initiated by an investigator based on a victim-reported wallet address or transaction.

**Attributes:**
- `case_id` (UUID, primary key)
- `case_number` (string, human-readable identifier)
- `title` (string)
- `reported_wallet_address` (string)
- `reported_transaction_hash` (string, optional)
- `blockchain` (string, e.g., "ethereum", "tron")
- `fraud_type` (enum: investment_scam, ransomware, sextortion, phishing, task_based_fraud, darknet, other)
- `reported_amount` (decimal, optional)
- `reported_asset` (string, e.g., "ETH", "USDT")
- `reported_date` (datetime)
- `created_at` (datetime)
- `updated_at` (datetime)
- `status` (enum: active, under_investigation, closed, archived)
- `investigator_id` (UUID, foreign key)
- `investigator_notes` (text, optional)

**Lifecycle:**
1. Created (investigator submits wallet/tx hash)
2. Active (tracing in progress)
3. Under Investigation (investigator analyzing results)
4. Closed (investigation complete)
5. Archived (historical record)

**Relationships:**
- One case has many wallets
- One case has many transactions
- One case has many evidence records
- One case has many notes
- One case produces one or more reports

---

### 2.2 Wallet

**Description:**  
Represents a blockchain wallet address discovered during investigation. May be the initial reported wallet, an intermediary, or a destination.

**Attributes:**
- `wallet_id` (UUID, primary key)
- `address` (string)
- `blockchain` (string)
- `label` (string, optional, e.g., "Initial Suspect Wallet")
- `wallet_type` (enum: suspect, intermediary, destination, unknown)
- `first_seen` (datetime)
- `last_activity` (datetime, nullable)
- `total_received` (decimal, nullable)
- `total_sent` (decimal, nullable)
- `transaction_count` (integer)
- `case_id` (UUID, foreign key)
- `discovered_at_hop` (integer, e.g., 0 for initial wallet, 1 for first hop, etc.)

**Relationships:**
- One wallet belongs to one case (in the context of that investigation)
- One wallet has many transactions (as sender or receiver)
- One wallet may have many entity candidates
- One wallet may have many patterns detected
- One wallet may have one risk score

---

### 2.3 Transaction

**Description:**  
Canonical representation of a blockchain transaction. Normalized from provider-specific formats.

**Attributes:**
- `transaction_id` (UUID, primary key)
- `transaction_hash` (string, unique per chain)
- `blockchain` (string)
- `block_number` (integer)
- `block_timestamp` (datetime)
- `from_address` (string)
- `to_address` (string, nullable for contract creation)
- `asset_symbol` (string, e.g., "ETH", "USDT", "TRX")
- `amount` (decimal)
- `token_contract_address` (string, nullable)
- `transaction_type` (enum: native_transfer, token_transfer, contract_call, contract_creation, internal_transfer)
- `gas_fee` (decimal)
- `gas_fee_asset` (string, e.g., "ETH")
- `status` (enum: confirmed, failed, pending)
- `confirmation_count` (integer)
- `provider_source` (string, e.g., "alchemy", "etherscan")
- `provider_timestamp` (datetime, when data was fetched)
- `raw_provider_data` (json, optional)
- `case_id` (UUID, foreign key)
- `discovered_at_hop` (integer)

**Canonical Transaction Normalization:**  
All chain-specific transaction formats (Ethereum, TRON, Solana, Bitcoin) normalize to this structure before storage.

**Relationships:**
- One transaction belongs to one case (in the context of that investigation)
- One transaction references one sender wallet
- One transaction references one receiver wallet
- One transaction may be part of one or more patterns
- One transaction may be pinned as evidence

---

### 2.4 Entity

**Description:**  
Represents a known or suspected real-world entity associated with one or more blockchain addresses (e.g., exchange, VASP, mixer, scam operator).

**Attributes:**
- `entity_id` (UUID, primary key)
- `name` (string, e.g., "Binance")
- `entity_type` (enum: exchange, vasp, mixer, bridge, defi_protocol, scam, darknet_market, individual, unknown)
- `description` (text, optional)
- `verification_status` (enum: verified, candidate, unverified, disputed)
- `confidence` (decimal, 0.0 to 1.0)
- `source` (string, e.g., "etherscan_labels", "manual_curation", "clustering_analysis")
- `external_references` (json, e.g., links to public databases)
- `first_seen` (datetime)
- `last_verified` (datetime, nullable)
- `created_at` (datetime)
- `updated_at` (datetime)

**Relationships:**
- One entity has many addresses
- One entity may appear in many cases
- One entity may have many attribution records

---

### 2.5 Address

**Description:**  
Links a blockchain address to an entity. An address may have multiple entity candidates.

**Attributes:**
- `address_id` (UUID, primary key)
- `blockchain` (string)
- `address` (string)
- `entity_id` (UUID, foreign key)
- `address_type` (enum: deposit, hot_wallet, cold_wallet, contract, unknown)
- `label` (string, optional, e.g., "Binance Hot Wallet 14")
- `confidence` (decimal, 0.0 to 1.0)
- `source` (string)
- `verified` (boolean)
- `first_seen` (datetime)
- `last_verified` (datetime, nullable)

**Relationships:**
- One address belongs to one entity (but multiple candidates may exist)
- One address appears in many transactions

---

### 2.6 Pattern

**Description:**  
Represents a detected suspicious pattern in wallet behavior or transaction flow.

**Attributes:**
- `pattern_id` (UUID, primary key)
- `pattern_type` (enum: peel_chain, rapid_forwarding, high_fan_in, high_fan_out, layering, consolidation, split_and_forward, mixer_interaction, bridge_interaction)
- `description` (text)
- `confidence` (decimal, 0.0 to 1.0)
- `wallet_id` (UUID, foreign key, nullable)
- `case_id` (UUID, foreign key)
- `detected_at` (datetime)
- `evidence` (json, references to transactions/wallets)
- `metrics` (json, e.g., {"fan_in_count": 47, "time_window_hours": 24})

**Relationships:**
- One pattern belongs to one case
- One pattern may reference one wallet
- One pattern references multiple transactions (via evidence JSON)

---

### 2.7 RiskScore

**Description:**  
Explainable risk score for a wallet in the context of a case investigation.

**Attributes:**
- `risk_score_id` (UUID, primary key)
- `wallet_id` (UUID, foreign key)
- `case_id` (UUID, foreign key)
- `score` (integer, 0-100)
- `risk_category` (enum: low, medium, high, critical)
- `scoring_version` (string, e.g., "v1.0")
- `calculated_at` (datetime)
- `factors` (json array of risk factors)

**Risk Factor Structure (JSON):**
```json
{
  "factor_type": "known_malicious_association",
  "weight": 25,
  "evidence": {
    "entity_id": "uuid",
    "source": "scamdb_record_4521"
  }
}
```

**Relationships:**
- One risk score belongs to one wallet
- One risk score belongs to one case
- One risk score references multiple transactions/entities (via factors JSON)

---

### 2.8 VASPAttribution

**Description:**  
Probabilistic attribution of a wallet address to a Virtual Asset Service Provider (VASP) or exchange.

**Attributes:**
- `attribution_id` (UUID, primary key)
- `wallet_id` (UUID, foreign key)
- `case_id` (UUID, foreign key)
- `candidate_entity_id` (UUID, foreign key)
- `confidence` (decimal, 0.0 to 1.0)
- `attribution_method` (enum: exact_match, cluster_match, behavioral_match, multi_signal)
- `evidence` (json array, supporting evidence)
- `source` (string)
- `attributed_at` (datetime)

**Evidence Structure (JSON):**
```json
[
  {
    "evidence_type": "exact_address_match",
    "reference": "address_id_uuid",
    "confidence_contribution": 0.5
  },
  {
    "evidence_type": "behavioral_similarity",
    "details": "high_transaction_volume_pattern",
    "confidence_contribution": 0.3
  }
]
```

**Relationships:**
- One attribution belongs to one wallet
- One attribution belongs to one case
- One attribution references one candidate entity

---

### 2.9 Graph

**Description:**  
Conceptual representation of the transaction graph for a case. May be persisted as structured data or computed on-demand.

**Attributes:**
- `graph_id` (UUID, primary key)
- `case_id` (UUID, foreign key)
- `root_wallet_address` (string)
- `blockchain` (string)
- `max_hop_depth` (integer)
- `branch_limit` (integer)
- `dust_threshold` (decimal)
- `time_window_start` (datetime, nullable)
- `time_window_end` (datetime, nullable)
- `node_count` (integer)
- `edge_count` (integer)
- `generated_at` (datetime)
- `graph_data` (json, nodes and edges)

**Graph Data Structure (JSON):**
```json
{
  "nodes": [
    {
      "id": "wallet_address",
      "type": "wallet",
      "label": "Suspect Wallet",
      "hop": 0
    }
  ],
  "edges": [
    {
      "source": "address_A",
      "target": "address_B",
      "transaction_hash": "0xabc...",
      "amount": 1200.00,
      "asset": "USDT",
      "timestamp": "2026-09-20T14:23:11Z"
    }
  ]
}
```

**Relationships:**
- One graph belongs to one case
- One graph references many wallets and transactions

---

### 2.10 Evidence

**Description:**  
Investigator-pinned transactions, wallets, or entities for preservation and reporting.

**Attributes:**
- `evidence_id` (UUID, primary key)
- `case_id` (UUID, foreign key)
- `evidence_type` (enum: transaction, wallet, entity, pattern, note)
- `reference_id` (UUID, references transaction_id, wallet_id, entity_id, or pattern_id)
- `investigator_note` (text)
- `pinned_at` (datetime)
- `investigator_id` (UUID, foreign key)

**Relationships:**
- One evidence record belongs to one case
- One evidence record references one transaction, wallet, entity, or pattern

---

### 2.11 Note

**Description:**  
Free-form investigator notes attached to a case.

**Attributes:**
- `note_id` (UUID, primary key)
- `case_id` (UUID, foreign key)
- `content` (text)
- `created_at` (datetime)
- `updated_at` (datetime)
- `investigator_id` (UUID, foreign key)

**Relationships:**
- One note belongs to one case

---

### 2.12 Report

**Description:**  
Generated investigation report summarizing case findings.

**Attributes:**
- `report_id` (UUID, primary key)
- `case_id` (UUID, foreign key)
- `report_type` (enum: summary, detailed, evidence_export)
- `format` (enum: pdf, json, html)
- `generated_at` (datetime)
- `generated_by` (UUID, foreign key to investigator)
- `content` (text or json, report data)
- `file_path` (string, nullable, for exported files)

**Relationships:**
- One report belongs to one case

---

### 2.13 Investigator

**Description:**  
User account for investigators using LedgerLens.

**Attributes:**
- `investigator_id` (UUID, primary key)
- `username` (string, unique)
- `email` (string, unique)
- `full_name` (string)
- `role` (enum: admin, investigator, viewer)
- `created_at` (datetime)
- `last_login` (datetime, nullable)
- `active` (boolean)

**Relationships:**
- One investigator has many cases
- One investigator creates many evidence records
- One investigator creates many notes
- One investigator generates many reports

---

## 3. Entity Relationships Diagram (Conceptual)

```
Investigator
    ↓ (creates)
Case
    ↓ (contains)
    ├── Wallet ──→ RiskScore
    │   ↓         ↓
    │   ├── Transaction
    │   ├── VASPAttribution → Entity → Address
    │   └── Pattern
    ├── Graph
    ├── Evidence (pins Transaction, Wallet, Entity, Pattern)
    ├── Note
    └── Report
```

---

## 4. Domain Terminology Glossary

### 4.1 Investigation Terms

**Case:**  
An investigation initiated by an investigator based on a victim-reported wallet or transaction.

**Suspect Wallet:**  
The initially reported wallet address associated with fraudulent activity.

**Intermediary Wallet:**  
A wallet used to forward, layer, or obfuscate fund flows between the suspect wallet and final destination.

**Destination Wallet:**  
A wallet identified as a likely endpoint for traced funds, often associated with a VASP or service.

**Hop:**  
One step in a multi-transaction trace. Hop 0 is the initial wallet, hop 1 includes direct counterparties, etc.

**Evidence:**  
Investigator-pinned transactions, wallets, entities, or patterns preserved for reporting.

---

### 4.2 Blockchain Terms

**Blockchain / Chain:**  
A distributed ledger network (e.g., Ethereum, TRON, Solana).

**Wallet / Address:**  
A blockchain account identifier (public address).

**Transaction:**  
A recorded transfer of value or interaction with a smart contract on a blockchain.

**Transaction Hash:**  
Unique identifier for a blockchain transaction.

**Block:**  
A group of transactions confirmed together on a blockchain.

**Token:**  
A digital asset implemented as a smart contract (e.g., ERC-20 on Ethereum, TRC-20 on TRON).

**Gas Fee:**  
Transaction fee paid to blockchain validators.

**Confirmation:**  
The number of blocks added after a transaction's block (higher = more secure).

---

### 4.3 Entity Terms

**VASP (Virtual Asset Service Provider):**  
An entity providing cryptocurrency services (exchanges, wallets, payment processors).

**Exchange:**  
A service allowing users to trade cryptocurrencies (e.g., Binance, Coinbase).

**Mixer / Tumbler:**  
A service designed to obfuscate transaction origins by pooling and redistributing funds.

**Bridge:**  
A service enabling cross-chain asset transfers.

**Entity:**  
A known or suspected real-world organization or individual associated with blockchain addresses.

**Entity Candidate:**  
A possible match for an address's controlling entity, with associated confidence.

**Confidence:**  
A probability score (0.0 to 1.0) representing certainty of entity attribution or pattern detection.

---

### 4.4 Pattern Terms

**Peel Chain:**  
A pattern where a wallet repeatedly sends small amounts to different addresses while retaining most funds, common in laundering.

**Rapid Forwarding:**  
Immediate or near-immediate transfer of received funds, suggesting intermediary behavior.

**Fan-In:**  
A wallet receiving funds from many sources in a short time window.

**Fan-Out:**  
A wallet distributing funds to many destinations in a short time window.

**Layering:**  
Multiple sequential transfers designed to obscure the fund origin.

**Consolidation:**  
Multiple wallets sending funds to a single destination.

**Split-and-Forward:**  
A wallet receiving funds and immediately splitting them to multiple destinations.

---

### 4.5 Risk Terms

**Risk Score:**  
A numerical value (0-100) representing the assessed risk level of a wallet.

**Risk Category:**  
A classification of risk level (low, medium, high, critical).

**Risk Factor:**  
A specific characteristic or behavior contributing to the risk score (e.g., "known malicious association").

**Explainability:**  
The ability to trace a risk score or classification to underlying evidence and logic.

---

## 5. Canonical Transaction Model Specification

### 5.1 Purpose

The Canonical Transaction Model is the single normalized representation of blockchain transactions consumed by all LedgerLens domain services.

### 5.2 Design Principles

1. **Chain-Agnostic:** Ethereum, TRON, Solana, Bitcoin transactions normalize to the same structure.
2. **Provider-Agnostic:** Alchemy, Etherscan, TronGrid responses normalize to the same structure.
3. **Complete:** Contains all information needed for graph, risk, attribution, and reporting.
4. **Immutable Reference:** Once normalized and persisted, the canonical record does not change (blockchain data is immutable).

### 5.3 Canonical Transaction Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transaction_id` | UUID | Yes | Internal primary key |
| `transaction_hash` | String | Yes | Blockchain transaction hash |
| `blockchain` | String | Yes | Chain identifier (ethereum, tron, solana, bitcoin) |
| `block_number` | Integer | Yes | Block containing transaction |
| `block_timestamp` | DateTime | Yes | Block confirmation timestamp |
| `from_address` | String | Yes | Sender address |
| `to_address` | String | Conditional | Receiver address (nullable for contract creation) |
| `asset_symbol` | String | Yes | Asset transferred (ETH, USDT, TRX, BTC, etc.) |
| `amount` | Decimal | Yes | Amount transferred |
| `token_contract_address` | String | Conditional | Token contract address (for token transfers) |
| `transaction_type` | Enum | Yes | Type of transaction (see below) |
| `gas_fee` | Decimal | Yes | Transaction fee paid |
| `gas_fee_asset` | String | Yes | Asset used for gas (ETH, TRX, etc.) |
| `status` | Enum | Yes | Transaction status (confirmed, failed, pending) |
| `confirmation_count` | Integer | Yes | Number of confirmations |
| `provider_source` | String | Yes | Data source (alchemy, etherscan, trongrid) |
| `provider_timestamp` | DateTime | Yes | When data was fetched |
| `raw_provider_data` | JSON | No | Original provider response (optional) |

### 5.4 Transaction Type Enum

- `native_transfer` — Native asset transfer (ETH, TRX, BTC)
- `token_transfer` — ERC-20, TRC-20, SPL token transfer
- `contract_call` — Smart contract interaction
- `contract_creation` — Smart contract deployment
- `internal_transfer` — Internal transaction (e.g., Ethereum internal tx)

### 5.5 Normalization Examples

**Ethereum ERC-20 USDT Transfer (Alchemy):**
```json
{
  "transaction_hash": "0xabc123...",
  "blockchain": "ethereum",
  "block_number": 18234567,
  "block_timestamp": "2026-09-20T14:23:11Z",
  "from_address": "0xA1B2C3...",
  "to_address": "0xD4E5F6...",
  "asset_symbol": "USDT",
  "amount": 1200.00,
  "token_contract_address": "0xdac17f958d2ee523a2206206994597c13d831ec7",
  "transaction_type": "token_transfer",
  "gas_fee": 0.0021,
  "gas_fee_asset": "ETH",
  "status": "confirmed",
  "confirmation_count": 15,
  "provider_source": "alchemy"
}
```

**TRON TRC-20 USDT Transfer (TronGrid):**
```json
{
  "transaction_hash": "def456...",
  "blockchain": "tron",
  "block_number": 51234567,
  "block_timestamp": "2026-09-21T10:15:03Z",
  "from_address": "TXyz123...",
  "to_address": "TAbc456...",
  "asset_symbol": "USDT",
  "amount": 500.00,
  "token_contract_address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
  "transaction_type": "token_transfer",
  "gas_fee": 13.5,
  "gas_fee_asset": "TRX",
  "status": "confirmed",
  "confirmation_count": 20,
  "provider_source": "trongrid"
}
```

**Key Point:**  
Both Ethereum and TRON USDT transfers have identical structure after normalization. Downstream services (graph engine, risk engine, frontend) consume them identically.

---

## 6. Graph Model Concepts

### 6.1 Graph Structure

**Nodes:**
- Wallet addresses
- Entities (when attributed)
- Smart contracts (if relevant)

**Edges:**
- Transactions (directed, from sender to receiver)
- Labeled with amount, asset, timestamp

### 6.2 Graph Traversal

**Breadth-First Search (BFS):**  
Starting from the suspect wallet, expand outward hop-by-hop, exploring all transactions at each hop level before moving deeper.

**Direction:**
- **Outbound:** Follow where funds were sent (default for fraud tracing)
- **Inbound:** Follow where funds came from (for source analysis)
- **Bidirectional:** Explore both directions

**Constraints:**
- **Max Hop Depth:** Stop after N hops (e.g., 5)
- **Branch Limit:** Limit transactions per wallet (e.g., top 50 by amount)
- **Dust Threshold:** Ignore transactions below minimum amount (e.g., <$10 equivalent)
- **Time Window:** Only include transactions within date range

### 6.3 Graph Metrics

- **Node Count:** Total wallets in graph
- **Edge Count:** Total transactions in graph
- **Path Length:** Number of hops from root to destination
- **Intermediary Count:** Number of wallets between root and VASP-attributed destination

---

## 7. Entity Lifecycle

### 7.1 Entity Creation

**Sources:**
- Manual curation (investigator adds known entity)
- External label import (Etherscan labels, public databases)
- Clustering analysis (future)
- Case linkage (repeated addresses across cases)

### 7.2 Entity Verification States

- **Verified:** Confirmed by trusted source (e.g., official exchange address list)
- **Candidate:** Probable match based on heuristics
- **Unverified:** Suggested by analysis, not confirmed
- **Disputed:** Conflicting information

### 7.3 Entity Updates

- Entities may gain additional addresses over time
- Confidence scores may change based on new evidence
- Last verified timestamp tracks data freshness

---

## 8. Domain Constraints

### 8.1 Data Integrity Constraints

- Transaction hash must be unique per blockchain
- Wallet address format must match blockchain validation rules
- Risk score must be between 0 and 100
- Confidence values must be between 0.0 and 1.0
- Timestamps must not be in the future

### 8.2 Business Logic Constraints

- A wallet cannot be both suspect and destination in the same case (classification may change during investigation)
- A transaction must reference existing from_address and to_address wallets
- A risk score must reference specific risk factors with evidence
- A VASP attribution must include confidence and evidence

### 8.3 Security Constraints

- Investigators can only access cases they created or are assigned to (future RBAC)
- Evidence records must reference valid case entities
- Reports cannot be modified after generation (append-only audit trail)

---

## 9. Domain Events (Future)

For event-driven architecture in later phases:

- `CaseCreated`
- `TransactionIngested`
- `GraphExpanded`
- `PatternDetected`
- `VASPAttributed`
- `RiskScoreCalculated`
- `EvidencePinned`
- `ReportGenerated`

These events enable asynchronous processing, background jobs, and real-time UI updates.

---

## 10. Summary

The LedgerLens domain model provides a clean separation between:
1. **Investigation domain** (Case, Evidence, Note, Report)
2. **Blockchain domain** (Transaction, Wallet, canonical model)
3. **Intelligence domain** (Entity, Pattern, RiskScore, VASPAttribution)
4. **Graph domain** (Graph structure, traversal)

This separation ensures:
- Clear ownership boundaries for specialist agents
- Single source of truth per concept
- Extensibility for new blockchains and patterns
- Maintainability through well-defined entities

---

**Document Status:** Initial domain model for Phase 0  
**Approval Required:** MASTER / CTO  
**Dependencies:** ARCHITECTURE.md
