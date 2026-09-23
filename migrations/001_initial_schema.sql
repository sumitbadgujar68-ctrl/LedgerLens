-- LedgerLens Phase 1 Migration
-- Migration: 001_initial_schema
-- Created: 2026-09-22
-- Purpose: Create foundational investigators and cases tables

-- investigators table
CREATE TABLE IF NOT EXISTS investigators (
    investigator_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'investigator', 'viewer')),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_investigators_username ON investigators(username);
CREATE INDEX idx_investigators_email ON investigators(email);

-- cases table
CREATE TABLE IF NOT EXISTS cases (
    case_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_number VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    reported_wallet_address VARCHAR(255) NOT NULL,
    reported_transaction_hash VARCHAR(255),
    blockchain VARCHAR(50) NOT NULL,
    fraud_type VARCHAR(100) NOT NULL,
    reported_amount NUMERIC(30, 8),
    reported_asset VARCHAR(50),
    reported_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL DEFAULT 'active' 
        CHECK (status IN ('active', 'under_investigation', 'closed', 'archived')),
    investigator_id UUID NOT NULL REFERENCES investigators(investigator_id),
    investigator_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cases_investigator ON cases(investigator_id);
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_blockchain ON cases(blockchain);
CREATE INDEX idx_cases_reported_wallet ON cases(reported_wallet_address);
CREATE INDEX idx_cases_created_at ON cases(created_at DESC);

-- Function to auto-generate case_number
CREATE OR REPLACE FUNCTION generate_case_number()
RETURNS TRIGGER AS $$
DECLARE
    next_seq INTEGER;
BEGIN
    SELECT COALESCE(MAX(CAST(SUBSTRING(case_number FROM 11) AS INTEGER)), 0) + 1
    INTO next_seq
    FROM cases
    WHERE case_number LIKE 'CASE-' || TO_CHAR(NEW.created_at, 'YYYY') || '-%';
    
    NEW.case_number := 'CASE-' || TO_CHAR(NEW.created_at, 'YYYY') || '-' || LPAD(next_seq::TEXT, 6, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_generate_case_number
BEFORE INSERT ON cases
FOR EACH ROW
WHEN (NEW.case_number IS NULL OR NEW.case_number = '')
EXECUTE FUNCTION generate_case_number();

-- Function to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_cases_updated_at
BEFORE UPDATE ON cases
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
