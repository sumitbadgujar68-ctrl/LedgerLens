# LedgerLens Database

## Overview

This directory contains database schema documentation and seed data for LedgerLens.

## Structure

- `schema/` - Database schema documentation
- `seeds/` - Seed data for development and testing

## Technology

- **Database**: PostgreSQL 15+
- **Infrastructure**: Supabase (managed PostgreSQL)
- **ORM**: SQLAlchemy 2.0+

## Migrations

Migration files are stored in the `migrations/` directory at the project root.

### Migration Naming Convention

```
NNN_description.sql          # Up migration
NNN_rollback.sql             # Down migration
```

### Current Migrations

- `001_initial_schema.sql` - Investigators and Cases tables (Phase 1)

## Connection

Database connection is configured via environment variables:

```
DATABASE_URL=postgresql://user:password@host:port/database
```

For local development, see `.env.example` in the backend directory.

## Schema Ownership

The database schema is the source of truth for data models. All schema changes must be:

1. Defined as migration files in `migrations/`
2. Documented in `docs/DATA_MODEL.md`
3. Reviewed by Database Engineer
4. Approved by MASTER before execution

## Phase 1 Schema

Phase 1 implements only:
- `investigators` table
- `cases` table
- Auto-generated case numbers (CASE-YYYY-NNNNNN)
- Basic indexes for performance

Future phases will add:
- `wallets`
- `transactions`
- `entities` and `addresses`
- `patterns`, `risk_scores`, `vasp_attributions`
- `graphs`, `evidence`, `notes`, `reports`, `jobs`

See `docs/DATA_MODEL.md` for complete schema specification.
