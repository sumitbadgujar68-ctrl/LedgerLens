-- LedgerLens Phase 6 Rollback Migration
-- Rollback for: 004_phase6_evidence
-- Purpose: Drop Phase 6 evidence store (reverse of 004_phase6_evidence.sql)

DROP TABLE IF EXISTS evidence;
