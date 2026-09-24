-- LedgerLens Phase 6 Migration
-- Migration: 005_phase6_reports_jobs
-- Created: 2026-09-25
-- Purpose: Report and background-job persistence (Phase 6 Step 3 — report schemas/models/persistence)
-- Approver: MASTER / CTO (Phase 6 Step 3)
-- Depends on: 001_initial_schema.sql (cases, investigators)
-- Spec: docs/DATA_MODEL.md sections 4.13 (reports), 4.14 (jobs)

-- ============================================================
-- 1. reports: Generated investigation reports
-- ============================================================
CREATE TABLE IF NOT EXISTS reports (
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

CREATE INDEX IF NOT EXISTS idx_reports_case ON reports(case_id);
CREATE INDEX IF NOT EXISTS idx_reports_generated_by ON reports(generated_by);
CREATE INDEX IF NOT EXISTS idx_reports_generated_at ON reports(generated_at DESC);

-- ============================================================
-- 2. jobs: Background job tracking (trace, graph expansion, report generation)
-- ============================================================
CREATE TABLE IF NOT EXISTS jobs (
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

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_case ON jobs(case_id);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at DESC);
