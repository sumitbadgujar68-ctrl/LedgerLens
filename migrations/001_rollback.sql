-- Rollback for Migration 001_initial_schema

DROP TRIGGER IF EXISTS trg_cases_updated_at ON cases;
DROP TRIGGER IF EXISTS trg_generate_case_number ON cases;
DROP FUNCTION IF EXISTS update_updated_at_column();
DROP FUNCTION IF EXISTS generate_case_number();

DROP INDEX IF EXISTS idx_cases_created_at;
DROP INDEX IF EXISTS idx_cases_reported_wallet;
DROP INDEX IF EXISTS idx_cases_blockchain;
DROP INDEX IF EXISTS idx_cases_status;
DROP INDEX IF EXISTS idx_cases_investigator;

DROP TABLE IF EXISTS cases;

DROP INDEX IF EXISTS idx_investigators_email;
DROP INDEX IF EXISTS idx_investigators_username;

DROP TABLE IF EXISTS investigators;
