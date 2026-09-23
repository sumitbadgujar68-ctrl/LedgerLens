-- LedgerLens Phase 4 Migration
-- Migration: 003_phase4_intelligence
-- Created: 2026-09-23
-- Purpose: Intelligence layer — entities, entity addresses, patterns, VASP attributions, risk scores
-- Approver: MASTER / CTO (Phase 4 Stage 1)
-- Depends on: 001_initial_schema.sql, 002_phase2_tracing.sql

-- ============================================================
-- 1. entities: Known organizations, exchanges, services, mixers
-- ============================================================
CREATE TABLE IF NOT EXISTS entities (
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

CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);

-- ============================================================
-- 2. entity_addresses: Curated address mappings with confidence and provenance
-- ============================================================
CREATE TABLE IF NOT EXISTS entity_addresses (
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

CREATE UNIQUE INDEX IF NOT EXISTS idx_entity_addresses_chain_addr ON entity_addresses(blockchain, address);
CREATE INDEX IF NOT EXISTS idx_entity_addresses_entity ON entity_addresses(entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_addresses_address ON entity_addresses(address);

-- ============================================================
-- 3. patterns: Detected structural patterns associated with a trace
-- ============================================================
CREATE TABLE IF NOT EXISTS patterns (
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

CREATE INDEX IF NOT EXISTS idx_patterns_trace ON patterns(trace_id);
CREATE INDEX IF NOT EXISTS idx_patterns_case ON patterns(case_id);
CREATE INDEX IF NOT EXISTS idx_patterns_wallet ON patterns(wallet_address);
CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(pattern_type);

-- ============================================================
-- 4. vasp_attributions: Attribution findings with provenance level and candidate evidence
-- ============================================================
CREATE TABLE IF NOT EXISTS vasp_attributions (
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

CREATE INDEX IF NOT EXISTS idx_vasp_attributions_trace ON vasp_attributions(trace_id);
CREATE INDEX IF NOT EXISTS idx_vasp_attributions_case ON vasp_attributions(case_id);
CREATE INDEX IF NOT EXISTS idx_vasp_attributions_wallet ON vasp_attributions(wallet_address);
CREATE INDEX IF NOT EXISTS idx_vasp_attributions_entity ON vasp_attributions(candidate_entity_id);

-- ============================================================
-- 5. risk_scores: Explainable scoring breakdown per wallet per trace
-- ============================================================
CREATE TABLE IF NOT EXISTS risk_scores (
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

CREATE UNIQUE INDEX IF NOT EXISTS idx_risk_scores_trace_wallet ON risk_scores(trace_id, wallet_address);
CREATE INDEX IF NOT EXISTS idx_risk_scores_case ON risk_scores(case_id);
CREATE INDEX IF NOT EXISTS idx_risk_scores_wallet ON risk_scores(wallet_address);
CREATE INDEX IF NOT EXISTS idx_risk_scores_category ON risk_scores(risk_category);
