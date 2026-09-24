-- LedgerLens Phase 6 Rollback Migration
-- Rollback for: 005_phase6_reports_jobs
-- Purpose: Drop report and background-job tables (reverse of 005_phase6_reports_jobs.sql)

DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS reports;
