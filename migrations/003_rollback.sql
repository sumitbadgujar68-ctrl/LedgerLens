-- LedgerLens Phase 4 Rollback Migration
-- Rollback for: 003_phase4_intelligence
-- Purpose: Safely drop intelligence layer tables in reverse dependency order

DROP TABLE IF EXISTS risk_scores CASCADE;
DROP TABLE IF EXISTS vasp_attributions CASCADE;
DROP TABLE IF EXISTS patterns CASCADE;
DROP TABLE IF EXISTS entity_addresses CASCADE;
DROP TABLE IF EXISTS entities CASCADE;
