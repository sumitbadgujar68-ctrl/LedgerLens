# LedgerLens Data Model

**Last Updated:** 2026-09-22  
**Phase:** PHASE 0 — FOUNDATION  
**Status:** Initial Conceptual Data Model

---

## 1. Overview

This document defines the conceptual database schema for LedgerLens. This is a Phase 0 architectural specification for PostgreSQL/Supabase, not a complete implementation (migrations will be created in Phase 1 by Database Engineer).

---

## 2. Database Technology

**Primary:** PostgreSQL 15+  
**Infrastructure:** Supabase (managed PostgreSQL)  
**ORM/Query Builder:** SQLAlchemy (Python backend)

**Rationale:**
- Strong relational model support
- JSON/JSONB for flexible data (patterns, evidence)
- Recursive CTEs for graph queries
- Strong constraint enforcement
- Supabase provides real-time subscriptions, auth, API

---

## 3. Schema Design Principles

### 3.1 Normalization
- Third normal form (3NF) for core entities
- Denormalization where read performance critical (graph data)
- JSON fields for flexible/evolving structures (evidence, risk factors)

### 3.2 Audit Trail
- `created_at` timestamp on all tables
- `updated_at` timestamp where applicable
- Soft deletes where appropriate (archive, not delete)

### 3.3 UUID Primary Keys
- All primary keys are UUID v4
- No auto-incrementing integers exposed
- Better for distributed systems and security

### 3.4 Foreign Key Constraints
- Enforce referential integrity at database level
- Cascade deletes where appropriate
- Restrict deletes where data preservation required

---

## 4. Core Tables

### 4.1 investigators

Investigator user accounts.

```sql
CREATE TABLE investigators (
    investigator_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username            VARCHAR(255) UNIQUE NOT NULL,
    email               VARCHAR(255) UNIQUE NOT NULL,
    password_hash       VARCHAR(255) NOT NULL,
    full_name           VARCHAR(255) NOT NULL,
    role                VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'investigator', 'viewer')),
    active              BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login          TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_investigators_username ON investigators(username);
CREATE INDEX idx_investigators_email ON investigators(email);
```

---

### 4.2 cases

Investigation cases.

```sql
CREATE TABLE cases (
    case_id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_number                 VARCHAR(50) UNIQUE NOT NULL,
    title                       VARCHAR(500) NOT NULL,
    reported_wallet_address     VARCHAR(255) NOT NULL,
    reported_transaction_hash   VARCHAR(255),
    blockchain                  VARCHAR(50) NOT NULL,
    fraud_type                  VARCHAR(100) NOT NULL,
    reported_amount             NUMERIC(30, 8),
    reported_asset              VARCHAR(50),
    reported_date               TIMESTAMP WITH TIME ZONE,
    status                      VARCHAR(50) NOT NULL DEFAULT 'active' 
                                CHECK (status IN ('active', 'under_investigation', 'closed', 'archived')),
    investigator_id             UUID NOT NULL REFERENCES investigators(investigator_id),
    investigator_notes          TEXT,
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at                  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cases_investigator ON cases(investigator_id);
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_blockchain ON cases(blockchain);
CREATE INDEX idx_cases_reported_wallet ON cases(reported_wallet_address);
CREATE INDEX idx_cases_created_at ON cases(created_at DESC);

-- Auto-generate case_number
-- Trigger to generate CASE-YYYY-NNNNNN format
```

---

### 4.3 wallets

Blockchain wallet addresses discovered during investigation.

```sql
CREATE TABLE wallets (
    wallet_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id             UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    address             VARCHAR(255) NOT NULL,
    blockchain          VARCHAR(50) NOT NULL,
    label               VARCHAR(255),
    wallet_type         VARCHAR(50) NOT NULL 
                        CHECK (wallet_type IN ('suspect', 'intermediary', 'destination', 'unknown')),
    discovered_at_hop   INTEGER NOT NULL DEFAULT 0,
    first_seen          TIMESTAMP WITH TIME ZONE,
    last_activity       TIMESTAMP WITH TIME ZONE,
    total_received      NUMERIC(30, 8),
    total_sent          NUMERIC(30, 8),
    transaction_count   INTEGER DEFAULT 0,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_wallets_case ON wallets(case_id);
CREATE INDEX idx_wallets_address ON wallets(address);
CREATE INDEX idx_wallets_blockchain ON wallets(blockchain);
CREATE INDEX idx_wallets_type ON wallets(wallet_type);
CREATE INDEX idx_wallets_hop ON wallets(discovered_at_hop);

-- Composite unique constraint: one wallet per address per case
CREATE UNIQUE INDEX idx_wallets_case_address ON wallets(case_id, address);
```

---

### 4.4 transactions

Normalized blockchain transactions.

```sql
CREATE TABLE transactions (
    transaction_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id                 UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    transaction_hash        VARCHAR(255) NOT NULL,
    blockchain              VARCHAR(50) NOT NULL,
    block_number            BIGINT NOT NULL,
    block_timestamp         TIMESTAMP WITH TIME ZONE NOT NULL,
    from_address            VARCHAR(255) NOT NULL,
    to_address              VARCHAR(255),
    asset_symbol            VARCHAR(50) NOT NULL,
    amount                  NUMERIC(30, 8) NOT NULL,
    token_contract_address  VARCHAR(255),
    transaction_type        VARCHAR(50) NOT NULL 
                            CHECK (transaction_type IN ('native_transfer', 'token_transfer', 
                                'contract_call', 'contract_creation', 'internal_transfer')),
    gas_fee                 NUMERIC(30, 8) NOT NULL,
    gas_fee_asset           VARCHAR(50) NOT NULL,
    status                  VARCHAR(50) NOT NULL DEFAULT 'confirmed' 
                            CHECK (status IN ('confirmed', 'failed', 'pending')),
    confirmation_count      INTEGER DEFAULT 0,
    provider_source         VARCHAR(100) NOT NULL,
    provider_timestamp      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    raw_provider_data       JSONB,
    discovered_at_hop       INTEGER NOT NULL,
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_transactions_case ON transactions(case_id);
CREATE INDEX idx_transactions_hash ON transactions(transaction_hash);
CREATE INDEX idx_transactions_blockchain ON transactions(blockchain);
CREATE INDEX idx_transactions_from ON transactions(from_address);
CREATE INDEX idx_transactions_to ON transactions(to_address);
CREATE INDEX idx_transactions_timestamp ON transactions(block_timestamp DESC);
CREATE INDEX idx_transactions_amount ON transactions(amount DESC);
CREATE INDEX idx_transactions_asset ON transactions(asset_symbol);
CREATE INDEX idx_transactions_hop ON transactions(discovered_at_hop);

-- Composite unique constraint: one tx per hash per blockchain per case
CREATE UNIQUE INDEX idx_transactions_case_hash ON transactions(case_id, blockchain, transaction_hash);
```

---

### 4.5 entities

Known or suspected real-world entities.

```sql
CREATE TABLE entities (
    entity_id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                    VARCHAR(255) NOT NULL,
    entity_type             VARCHAR(100) NOT NULL 
                            CHECK (entity_type IN ('exchange', 'vasp', 'mixer', 'bridge', 
                                'defi_protocol', 'scam', 'darknet_market', 'individual', 'unknown')),
    description             TEXT,
    verification_status     VARCHAR(50) NOT NULL DEFAULT 'unverified' 
                            CHECK (verification_status IN ('verified', 'candidate', 'unverified', 'disputed')),
    confidence              NUMERIC(3, 2) CHECK (confidence BETWEEN 0.0 AND 1.0),
    source                  VARCHAR(255),
    external_references     JSONB,
    first_seen              TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_verified           TIMESTAMP WITH TIME ZONE,
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_entities_name ON entities(name);
CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_verification ON entities(verification_status);
```

---

### 4.6 addresses

Links blockchain addresses to entities.

```sql
CREATE TABLE addresses (
    address_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id           UUID NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
    blockchain          VARCHAR(50) NOT NULL,
    address             VARCHAR(255) NOT NULL,
    address_type        VARCHAR(100) 
                        CHECK (address_type IN ('deposit', 'hot_wallet', 'cold_wallet', 'contract', 'unknown')),
    label               VARCHAR(255),
    confidence          NUMERIC(3, 2) CHECK (confidence BETWEEN 0.0 AND 1.0),
    source              VARCHAR(255),
    verified            BOOLEAN DEFAULT FALSE,
    first_seen          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_verified       TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_addresses_entity ON addresses(entity_id);
CREATE INDEX idx_addresses_blockchain ON addresses(blockchain);
CREATE INDEX idx_addresses_address ON addresses(address);

-- Composite unique constraint: one address per blockchain per entity
CREATE UNIQUE INDEX idx_addresses_blockchain_address_entity ON addresses(blockchain, address, entity_id);
```

---

### 4.6 entities & entity_addresses (Phase 4 Migration 003)

Curated known organizations, exchanges, services, and associated blockchain addresses.

```sql
CREATE TABLE entities (
    entity_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(255) NOT NULL UNIQUE,
    entity_type         VARCHAR(50) NOT NULL CHECK (entity_type IN (
                        'exchange', 'vasp', 'mixer', 'bridge', 'defi_protocol', 
                        'payment_processor', 'scam_infrastructure', 'known_contract', 'unknown')),
    jurisdiction        VARCHAR(100),
    website             VARCHAR(255),
    verification_level  VARCHAR(50) NOT NULL DEFAULT 'unverified',
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE entity_addresses (
    address_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id           UUID NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
    blockchain          VARCHAR(50) NOT NULL DEFAULT 'ethereum',
    address             VARCHAR(255) NOT NULL,
    label               VARCHAR(255),
    category            VARCHAR(50),
    source              VARCHAR(100) NOT NULL,
    source_url          TEXT,
    confidence          NUMERIC(3, 2) NOT NULL DEFAULT 1.00 CHECK (confidence BETWEEN 0.0 AND 1.0),
    first_seen          TIMESTAMP WITH TIME ZONE,
    last_verified       TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata            JSONB DEFAULT '{}'::jsonb,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_entity_addresses_chain_addr ON entity_addresses(blockchain, address);
CREATE INDEX idx_entity_addresses_entity ON entity_addresses(entity_id);
CREATE INDEX idx_entity_addresses_address ON entity_addresses(address);
```

---

### 4.7 patterns (Phase 4 Migration 003)

Detected graph and temporal patterns for a specific trace run.

```sql
CREATE TABLE patterns (
    pattern_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id             UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    trace_id            UUID NOT NULL REFERENCES trace_runs(trace_id) ON DELETE CASCADE,
    wallet_address      VARCHAR(255) NOT NULL,
    pattern_type        VARCHAR(100) NOT NULL CHECK (pattern_type IN (
                        'rapid_forwarding', 'peel_chain', 'high_fan_out', 'high_fan_in', 
                        'cyclic_flow', 'repeated_counterparties', 'volume_concentration')),
    confidence          NUMERIC(3, 2) NOT NULL DEFAULT 1.00 CHECK (confidence BETWEEN 0.0 AND 1.0),
    description         TEXT NOT NULL,
    evidence            JSONB NOT NULL,
    metrics             JSONB DEFAULT '{}'::jsonb,
    detected_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_patterns_trace ON patterns(trace_id);
CREATE INDEX idx_patterns_case ON patterns(case_id);
CREATE INDEX idx_patterns_wallet ON patterns(wallet_address);
CREATE INDEX idx_patterns_type ON patterns(pattern_type);
```

---

### 4.8 risk_scores (Phase 4 Migration 003)

Explainable risk scores and itemized factor breakdowns per wallet per trace.

```sql
CREATE TABLE risk_scores (
    risk_score_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id             UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    trace_id            UUID NOT NULL REFERENCES trace_runs(trace_id) ON DELETE CASCADE,
    wallet_address      VARCHAR(255) NOT NULL,
    score               INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
    risk_category       VARCHAR(50) NOT NULL CHECK (risk_category IN ('low', 'medium', 'high', 'critical')),
    scoring_version     VARCHAR(50) NOT NULL DEFAULT 'v1.0.0',
    factors             JSONB NOT NULL,
    calculated_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_risk_scores_trace_wallet ON risk_scores(trace_id, wallet_address);
CREATE INDEX idx_risk_scores_case ON risk_scores(case_id);
CREATE INDEX idx_risk_scores_wallet ON risk_scores(wallet_address);
CREATE INDEX idx_risk_scores_category ON risk_scores(risk_category);
```

---

### 4.9 vasp_attributions (Phase 4 Migration 003)

VASP and entity attribution records with multi-signal evidence and confidence levels.

```sql
CREATE TABLE vasp_attributions (
    attribution_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id             UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    trace_id            UUID NOT NULL REFERENCES trace_runs(trace_id) ON DELETE CASCADE,
    wallet_address      VARCHAR(255) NOT NULL,
    candidate_entity_id UUID NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
    provenance_level    VARCHAR(20) NOT NULL CHECK (provenance_level IN ('DIRECT', 'SUPPORTED', 'INFERRED', 'UNKNOWN')),
    confidence          NUMERIC(3, 2) NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),
    attribution_method  VARCHAR(100) NOT NULL CHECK (attribution_method IN (
                        'registry_exact_match', 'contract_signature', 'deposit_sweep_heuristic', 'multi_signal')),
    evidence            JSONB NOT NULL,
    source              VARCHAR(255) NOT NULL,
    attributed_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_vasp_attributions_trace ON vasp_attributions(trace_id);
CREATE INDEX idx_vasp_attributions_case ON vasp_attributions(case_id);
CREATE INDEX idx_vasp_attributions_wallet ON vasp_attributions(wallet_address);
CREATE INDEX idx_vasp_attributions_entity ON vasp_attributions(candidate_entity_id);
```

---

### 4.10 graphs

Transaction graph metadata and data.

```sql
CREATE TABLE graphs (
    graph_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id             UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    root_wallet_address VARCHAR(255) NOT NULL,
    blockchain          VARCHAR(50) NOT NULL,
    max_hop_depth       INTEGER NOT NULL,
    branch_limit        INTEGER,
    dust_threshold      NUMERIC(30, 8),
    time_window_start   TIMESTAMP WITH TIME ZONE,
    time_window_end     TIMESTAMP WITH TIME ZONE,
    node_count          INTEGER DEFAULT 0,
    edge_count          INTEGER DEFAULT 0,
    graph_data          JSONB NOT NULL,
    generated_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_graphs_case ON graphs(case_id);
CREATE INDEX idx_graphs_generated ON graphs(generated_at DESC);

-- One primary graph per case (may have versions)
```

---

### 4.11 evidence

Investigator-pinned evidence.

```sql
CREATE TABLE evidence (
    evidence_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id             UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    evidence_type       VARCHAR(50) NOT NULL 
                        CHECK (evidence_type IN ('transaction', 'wallet', 'entity', 'pattern', 'note')),
    reference_id        UUID NOT NULL,
    investigator_note   TEXT,
    investigator_id     UUID NOT NULL REFERENCES investigators(investigator_id),
    pinned_at           TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_evidence_case ON evidence(case_id);
CREATE INDEX idx_evidence_type ON evidence(evidence_type);
CREATE INDEX idx_evidence_reference ON evidence(reference_id);
CREATE INDEX idx_evidence_investigator ON evidence(investigator_id);
CREATE INDEX idx_evidence_pinned ON evidence(pinned_at DESC);
```

---

### 4.12 notes

Investigator notes for cases.

```sql
CREATE TABLE notes (
    note_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id             UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    investigator_id     UUID NOT NULL REFERENCES investigators(investigator_id),
    content             TEXT NOT NULL,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_notes_case ON notes(case_id);
CREATE INDEX idx_notes_investigator ON notes(investigator_id);
CREATE INDEX idx_notes_created ON notes(created_at DESC);
```

---

### 4.13 reports

Generated investigation reports.

```sql
CREATE TABLE reports (
    report_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id             UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    report_type         VARCHAR(50) NOT NULL 
                        CHECK (report_type IN ('summary', 'detailed', 'evidence_export')),
    format              VARCHAR(50) NOT NULL CHECK (format IN ('pdf', 'json', 'html')),
    content             TEXT,
    file_path           VARCHAR(500),
    generated_by        UUID NOT NULL REFERENCES investigators(investigator_id),
    generated_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_reports_case ON reports(case_id);
CREATE INDEX idx_reports_generated_by ON reports(generated_by);
CREATE INDEX idx_reports_generated_at ON reports(generated_at DESC);
```

---

### 4.14 jobs

Background job tracking (trace, graph expansion, report generation).

```sql
CREATE TABLE jobs (
    job_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type            VARCHAR(100) NOT NULL CHECK (job_type IN ('trace', 'graph_expansion', 
                            'report_generation', 'entity_enrichment')),
    status              VARCHAR(50) NOT NULL DEFAULT 'queued' 
                        CHECK (status IN ('queued', 'processing', 'completed', 'failed')),
    progress            INTEGER DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    case_id             UUID REFERENCES cases(case_id) ON DELETE CASCADE,
    initiated_by        UUID NOT NULL REFERENCES investigators(investigator_id),
    parameters          JSONB,
    result              JSONB,
    error_message       TEXT,
    started_at          TIMESTAMP WITH TIME ZONE,
    completed_at        TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_case ON jobs(case_id);
CREATE INDEX idx_jobs_created ON jobs(created_at DESC);
```

---

## 5. Relationships Summary

```
investigators
    ↓ (1:N)
cases
    ↓ (1:N)
    ├── wallets ──→ risk_scores (1:1)
    │   ↓           ↓
    │   └── vasp_attributions ──→ entities ──→ addresses
    ├── transactions
    ├── patterns
    ├── graphs
    ├── evidence
    ├── notes
    ├── reports
    └── jobs
```

---

## 6. Data Flow Patterns

### 6.1 Case Creation Flow

1. INSERT into `cases` (investigator input)
2. INSERT initial wallet into `wallets` (hop 0)
3. CREATE background job in `jobs` (trace job)
4. Background worker fetches transactions from blockchain
5. INSERT transactions into `transactions`
6. INSERT discovered wallets into `wallets` (hop 1, 2, ...)
7. UPDATE job status to 'completed'

---

### 6.2 Graph Generation Flow

1. SELECT all wallets and transactions for case
2. Build graph structure in memory (nodes/edges)
3. INSERT into `graphs` with JSONB graph_data
4. Frontend queries graph via `GET /cases/{case_id}/graph`

---

### 6.3 Risk Scoring Flow

1. SELECT wallet and related transactions
2. Calculate risk factors (pattern analysis)
3. INSERT into `risk_scores` with factors JSONB
4. Frontend displays risk score with factor breakdown

---

## 7. Indexing Strategy

### 7.1 Primary Indexes

All foreign keys have indexes for join performance:
- `case_id` on all case-related tables
- `investigator_id` on investigator-related tables
- `wallet_id`, `entity_id` on related tables

### 7.2 Query-Specific Indexes

- Transaction timestamp (DESC) for timeline queries
- Transaction amount (DESC) for top-amount queries
- Risk score (DESC) for high-risk wallet queries
- Address lookups for entity matching

### 7.3 Composite Indexes

- `(case_id, address)` on wallets (uniqueness + lookup)
- `(case_id, blockchain, transaction_hash)` on transactions (uniqueness)
- `(blockchain, address)` on addresses (entity lookup)

---

## 8. JSON/JSONB Fields

### 8.1 patterns.evidence

```json
{
  "transactions": ["tx_hash_1", "tx_hash_2"],
  "wallets": ["wallet_id_1", "wallet_id_2"],
  "details": "Detected 8 sequential transfers with decreasing amounts"
}
```

### 8.2 risk_scores.factors

```json
[
  {
    "factor_type": "rapid_onward_transfer",
    "weight": 20,
    "evidence": {
      "transaction_hash": "0xABC...",
      "time_delta_hours": 1.5
    }
  },
  {
    "factor_type": "known_malicious_association",
    "weight": 25,
    "evidence": {
      "entity_id": "uuid",
      "source": "scamdb_record_4521"
    }
  }
]
```

### 8.3 vasp_attributions.evidence

```json
[
  {
    "evidence_type": "exact_address_match",
    "reference": "address_id_uuid",
    "confidence_contribution": 0.5
  },
  {
    "evidence_type": "cluster_match",
    "details": "Address belongs to known Binance cluster",
    "confidence_contribution": 0.32
  }
]
```

### 8.4 graphs.graph_data

```json
{
  "nodes": [
    {"id": "0xABC...", "type": "wallet", "hop": 0, "label": "Suspect Wallet"}
  ],
  "edges": [
    {
      "source": "0xABC...",
      "target": "0xDEF...",
      "transaction_hash": "0x123...",
      "amount": "1200.00",
      "asset": "USDT"
    }
  ]
}
```

---

## 9. Constraints & Validations

### 9.1 Check Constraints

- Risk scores between 0-100
- Confidence values between 0.0-1.0
- Job progress between 0-100
- Enum values validated

### 9.2 Foreign Key Constraints

- ON DELETE CASCADE for case-related data (delete case = delete wallets/transactions)
- ON DELETE RESTRICT for investigators (prevent deleting investigator with cases)

### 9.3 Unique Constraints

- One wallet per address per case
- One transaction per hash per blockchain per case
- One risk score per wallet per case
- Unique case numbers

---

## 10. Migration Strategy

### 10.1 Phase 1 Migrations

**Migration 001:** Create investigators, cases tables  
**Migration 002:** Create wallets, transactions tables  
**Migration 003:** Create entities, addresses tables  
**Migration 004:** Create patterns, risk_scores, vasp_attributions tables  
**Migration 005:** Create graphs, evidence, notes, reports, jobs tables  
**Migration 006:** Create indexes  
**Migration 007:** Create triggers (case_number generation, updated_at)

### 10.2 Rollback Strategy

All migrations must include DOWN migration for rollback.

### 10.3 Seed Data

- Demo investigator account
- Known entity registry (Binance, Coinbase, Tornado Cash, etc.)
- Known addresses for MVP testing

---

## 11. Performance Considerations

### 11.1 Query Optimization

- Use prepared statements (SQLAlchemy ORM)
- Paginate large result sets
- Index foreign keys
- Avoid SELECT * (select only needed columns)

### 11.2 Connection Pooling

- SQLAlchemy connection pool
- Supabase handles connection management

### 11.3 Caching

- Redis for frequently accessed entity lookups
- Application-level caching for immutable blockchain data

---

## 12. Security Considerations

### 12.1 Sensitive Data

- Password hashes only (bcrypt)
- No private keys stored (system never handles private keys)
- API keys in environment variables, not database

### 12.2 Access Control

- Row-level security (RLS) in Supabase (future)
- Investigators can only access their own cases (application-level in MVP)

### 12.3 Audit Logging

- All case modifications logged via created_at/updated_at
- Evidence table preserves pinned_at timestamps
- Job table preserves initiated_by

---

## 13. Backup & Recovery

### 13.1 Backup Strategy

- Supabase automated daily backups
- Point-in-time recovery supported
- Export critical data (cases, evidence) for offline storage

### 13.2 Data Retention

- Active cases: indefinite
- Closed cases: retain for N years (configurable)
- Archived cases: compressed storage
- Jobs: purge completed jobs after 30 days (configurable)

---

## 14. Future Enhancements

### 14.1 Phase 2+ Additions

- `cross_chain_traces` table (track cross-chain movements)
- `alerts` table (automated alert triggers)
- `case_assignments` table (multi-investigator collaboration)
- `audit_logs` table (comprehensive audit trail)

### 14.2 Denormalization

- Materialized views for dashboard statistics
- Cached graph representations
- Pre-computed risk score summaries

---

**Document Status:** Initial conceptual data model for Phase 0  
**Approval Required:** MASTER / CTO  
**Dependencies:** ARCHITECTURE.md, DOMAIN_MODEL.md  
**Implementation:** Database Engineer (Phase 1)
