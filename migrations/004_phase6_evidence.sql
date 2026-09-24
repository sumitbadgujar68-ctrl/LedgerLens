-- LedgerLens Phase 6 Migration
-- Migration: 004_phase6_evidence
-- Created: 2026-09-25
-- Purpose: Evidence store for investigation reports (Phase 6 Step 2 — evidence/report aggregation)
-- Approver: MASTER / CTO (Phase 6 Step 2)
-- Depends on: 001_initial_schema.sql (cases, investigators)
-- Spec: docs/DATA_MODEL.md section 4.11 (evidence)

-- ============================================================
-- 1. evidence: Investigator-pinned evidence for cases
-- ============================================================
CREATE TABLE IF NOT EXISTS evidence (
    evidence_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id             UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    evidence_type       VARCHAR(50) NOT NULL
                        CHECK (evidence_type IN ('transaction', 'wallet', 'entity', 'pattern', 'note')),
    reference_id        UUID NOT NULL,
    investigator_note   TEXT,
    investigator_id     UUID NOT NULL REFERENCES investigators(investigator_id),
    pinned_at           TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evidence_case ON evidence(case_id);
CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence(evidence_type);
CREATE INDEX IF NOT EXISTS idx_evidence_reference ON evidence(reference_id);
CREATE INDEX IF NOT EXISTS idx_evidence_investigator ON evidence(investigator_id);
CREATE INDEX IF NOT EXISTS idx_evidence_pinned ON evidence(pinned_at DESC);
