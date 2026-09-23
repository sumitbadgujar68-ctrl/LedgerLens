-- LedgerLens Phase 2 Migration
-- Migration: 002_phase2_tracing
-- Created: 2026-09-23
-- Purpose: Trace runs, canonical transaction storage, graph persistence
-- Approver: MASTER / CTO (Phase-2 schema extension)
-- Depends on: 001_initial_schema.sql (cases, investigators)

-- ============================================================
-- trace_runs: Phase-2 trace execution records
-- (async-ready status field; Phase 2 may complete inline)
-- ============================================================
CREATE TABLE IF NOT EXISTS trace_runs (
    trace_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id             UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    start_wallet_address VARCHAR(255) NOT NULL,
    blockchain          VARCHAR(50) NOT NULL DEFAULT 'ethereum',
    direction           VARCHAR(20) NOT NULL DEFAULT 'outbound'
                        CHECK (direction IN ('outbound', 'inbound', 'both')),
    max_hops            INTEGER NOT NULL DEFAULT 3 CHECK (max_hops BETWEEN 1 AND 10),
    max_branches        INTEGER NOT NULL DEFAULT 25 CHECK (max_branches BETWEEN 1 AND 500),
    min_amount          NUMERIC(78, 18),
    asset_filters       JSONB,
    time_range_start    TIMESTAMP WITH TIME ZONE,
    time_range_end      TIMESTAMP WITH TIME ZONE,
    status              VARCHAR(50) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'running', 'completed', 'partial', 'failed')),
    result_status       VARCHAR(50),
    provider            VARCHAR(50),
    summary             JSONB DEFAULT '{}'::jsonb,
    errors              JSONB DEFAULT '[]'::jsonb,
    parameters          JSONB DEFAULT '{}'::jsonb,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at        TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_trace_runs_case ON trace_runs(case_id);
CREATE INDEX IF NOT EXISTS idx_trace_runs_status ON trace_runs(status);
CREATE INDEX IF NOT EXISTS idx_trace_runs_created ON trace_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_trace_runs_wallet ON trace_runs(start_wallet_address);

-- ============================================================
-- graphs: canonical graph per trace (JSONB nodes/edges)
-- ============================================================
CREATE TABLE IF NOT EXISTS graphs (
    graph_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id             UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    trace_id            UUID REFERENCES trace_runs(trace_id) ON DELETE CASCADE,
    root_wallet_address VARCHAR(255) NOT NULL,
    blockchain          VARCHAR(50) NOT NULL DEFAULT 'ethereum',
    max_hop_depth       INTEGER NOT NULL DEFAULT 0,
    branch_limit        INTEGER,
    dust_threshold      NUMERIC(78, 18),
    time_window_start   TIMESTAMP WITH TIME ZONE,
    time_window_end     TIMESTAMP WITH TIME ZONE,
    node_count          INTEGER DEFAULT 0,
    edge_count          INTEGER DEFAULT 0,
    graph_data          JSONB NOT NULL,
    generated_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_graphs_case ON graphs(case_id);
CREATE INDEX IF NOT EXISTS idx_graphs_trace ON graphs(trace_id);
CREATE INDEX IF NOT EXISTS idx_graphs_generated ON graphs(generated_at DESC);

-- ============================================================
-- transactions: canonical transaction storage per case/trace
-- Deviations from DATA_MODEL 4.4 (Phase-2 pragmatic extensions):
--   - amount NUMERIC(78,18) for full crypto precision (not 30,8)
--   - block_number/timestamp/gas nullable (provider may omit)
--   - status includes 'unknown' (receipt status not always available)
--   - transaction_type uses canonical transfer/contract_interaction/unknown
--   - unique per (case_id, blockchain, hash, from, to, provider_reference)
--     to allow multiple transfer events in one tx (ERC logs)
-- ============================================================
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id             UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    trace_id            UUID REFERENCES trace_runs(trace_id) ON DELETE SET NULL,
    transaction_hash    VARCHAR(255) NOT NULL,
    blockchain          VARCHAR(50) NOT NULL,
    block_number        BIGINT,
    block_timestamp     TIMESTAMP WITH TIME ZONE,
    from_address        VARCHAR(255) NOT NULL,
    to_address          VARCHAR(255),
    asset_symbol        VARCHAR(50),
    asset_type          VARCHAR(50),
    amount              NUMERIC(78, 18) NOT NULL DEFAULT 0,
    decimals            INTEGER NOT NULL DEFAULT 18,
    token_contract_address VARCHAR(255),
    transfer_category   VARCHAR(50),
    transaction_type    VARCHAR(50) NOT NULL DEFAULT 'transfer',
    status              VARCHAR(50) NOT NULL DEFAULT 'unknown',
    gas_used            BIGINT,
    max_fee_per_gas     NUMERIC(78, 18),
    priority_fee_per_gas NUMERIC(78, 18),
    total_fee           NUMERIC(78, 18),
    provider_source     VARCHAR(100) NOT NULL,
    provider_reference  VARCHAR(512) NOT NULL,
    raw_reference       TEXT,
    discovered_at_hop   INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_case ON transactions(case_id);
CREATE INDEX IF NOT EXISTS idx_transactions_trace ON transactions(trace_id);
CREATE INDEX IF NOT EXISTS idx_transactions_hash ON transactions(transaction_hash);
CREATE INDEX IF NOT EXISTS idx_transactions_blockchain ON transactions(blockchain);
CREATE INDEX IF NOT EXISTS idx_transactions_from ON transactions(from_address);
CREATE INDEX IF NOT EXISTS idx_transactions_to ON transactions(to_address);
CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(block_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_amount ON transactions(amount DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_asset ON transactions(asset_symbol);
CREATE INDEX IF NOT EXISTS idx_transactions_hop ON transactions(discovered_at_hop);

CREATE UNIQUE INDEX IF NOT EXISTS idx_transactions_unique_event
    ON transactions(case_id, blockchain, transaction_hash, from_address, to_address, provider_reference);
