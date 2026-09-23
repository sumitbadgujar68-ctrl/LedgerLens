-- Rollback for Migration 002_phase2_tracing
-- Safe to run after 002; does not touch Phase-1 tables

DROP INDEX IF EXISTS idx_transactions_unique_event;
DROP INDEX IF EXISTS idx_transactions_hop;
DROP INDEX IF EXISTS idx_transactions_asset;
DROP INDEX IF EXISTS idx_transactions_amount;
DROP INDEX IF EXISTS idx_transactions_timestamp;
DROP INDEX IF EXISTS idx_transactions_to;
DROP INDEX IF EXISTS idx_transactions_from;
DROP INDEX IF EXISTS idx_transactions_blockchain;
DROP INDEX IF EXISTS idx_transactions_hash;
DROP INDEX IF EXISTS idx_transactions_trace;
DROP INDEX IF EXISTS idx_transactions_case;
DROP TABLE IF EXISTS transactions;

DROP INDEX IF EXISTS idx_graphs_generated;
DROP INDEX IF EXISTS idx_graphs_trace;
DROP INDEX IF EXISTS idx_graphs_case;
DROP TABLE IF EXISTS graphs;

DROP INDEX IF EXISTS idx_trace_runs_wallet;
DROP INDEX IF EXISTS idx_trace_runs_created;
DROP INDEX IF EXISTS idx_trace_runs_status;
DROP INDEX IF EXISTS idx_trace_runs_case;
DROP TABLE IF EXISTS trace_runs;
