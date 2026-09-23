# LedgerLens Architectural Decisions

**Last Updated:** 2026-09-23  
**Phase:** PHASE 1 — CASE FOUNDATION (CLOSED)  
**Status:** ADRs + Phase 1 completion record

---

## 1. Overview

This document records key architectural decisions for LedgerLens, including rationale, alternatives considered, and trade-offs. Each decision follows the ADR (Architectural Decision Record) format.

---

## ADR Template

```
## ADR-NNN: [Decision Title]

**Status:** Proposed | Accepted | Deprecated | Superseded  
**Date:** YYYY-MM-DD  
**Deciders:** [Who made this decision]

### Context
[What is the issue/problem we're addressing?]

### Decision
[What is the decision we're making?]

### Rationale
[Why are we making this decision?]

### Alternatives Considered
[What other options did we evaluate?]

### Consequences
[What are the implications of this decision?]

### Trade-offs
[What are we gaining/losing?]
```

---

## ADR-001: Provider-Agnostic Blockchain Architecture

**Status:** Accepted  
**Date:** 2026-09-22  
**Deciders:** System Architect, MASTER

### Context

LedgerLens requires access to blockchain transaction data. Multiple blockchain data providers exist (Alchemy, Etherscan, Infura, TronGrid, etc.) with varying pricing, rate limits, and feature sets. The system must support multiple blockchains (Ethereum, TRON, Solana, Bitcoin).

Coupling directly to a single provider creates vendor lock-in and makes it difficult to:
- Switch providers if pricing/availability changes
- Use multiple providers for enrichment/fallback
- Add new blockchains with different provider ecosystems

### Decision

Implement a provider-agnostic blockchain architecture with three abstraction layers:

1. **BlockchainAdapter Interface** — Chain-agnostic interface consumed by domain services
2. **Chain-Specific Adapters** — Ethereum Adapter, TRON Adapter, etc.
3. **Provider Abstraction** — Alchemy Provider, Etherscan Provider, TronGrid Provider, etc.

```
Domain Services (Graph, Risk, Attribution)
        ↓
BlockchainAdapter Interface
        ↓
EthereumAdapter | TronAdapter | SolanaAdapter
        ↓
AlchemyProvider | EtherscanProvider | TronGridProvider
        ↓
External APIs
```

### Rationale

- **Extensibility:** Add new chains by implementing adapter interface
- **Flexibility:** Swap providers without rewriting domain logic
- **Reliability:** Use multiple providers for fallback/enrichment
- **Testability:** Mock adapters for unit testing
- **Maintainability:** Provider-specific logic isolated from core system

### Alternatives Considered

**Alternative 1: Direct provider coupling**
- Pros: Simpler initial implementation
- Cons: Vendor lock-in, difficult to swap providers, hard to test

**Alternative 2: Middleware blockchain indexer (self-hosted)**
- Pros: Full control, no rate limits
- Cons: Infrastructure complexity, maintenance burden, out of MVP scope

**Alternative 3: Commercial blockchain intelligence platform SDK**
- Pros: Rich features
- Cons: Expensive, vendor lock-in, defeats purpose of building LedgerLens

### Consequences

- **Positive:** Clean separation of concerns, future-proof architecture
- **Negative:** Additional abstraction layers increase initial implementation complexity

### Trade-offs

**Gain:** Flexibility, extensibility, testability  
**Lose:** Slightly more complex initial implementation (acceptable for long-term benefit)

---

## ADR-002: Canonical Transaction Model

**Status:** Accepted  
**Date:** 2026-09-22  
**Deciders:** System Architect, MASTER

### Context

Different blockchains have different transaction formats:
- Ethereum: from, to, value, input, gas, etc.
- TRON: from, to, amount, contract, fee_limit, etc.
- Solana: signatures, instructions, accounts, etc.
- Bitcoin: inputs, outputs, fees, etc.

Different providers return different response formats even for the same blockchain.

Domain services (graph engine, risk engine, VASP attribution) need consistent transaction representation.

### Decision

Define a **Canonical Transaction Model** that all provider responses normalize to before storage and consumption by downstream services.

All chain-specific and provider-specific formats convert to:
```
{
  transaction_id: UUID,
  transaction_hash: string,
  blockchain: string,
  block_number: integer,
  block_timestamp: datetime,
  from_address: string,
  to_address: string,
  asset_symbol: string,
  amount: decimal,
  token_contract_address: string | null,
  transaction_type: enum,
  gas_fee: decimal,
  gas_fee_asset: string,
  status: enum,
  provider_source: string,
  raw_provider_data: json (optional)
}
```

### Rationale

- **Single Source of Truth:** One transaction representation consumed by all services
- **Chain-Agnostic Services:** Graph engine works identically for Ethereum and TRON
- **Simplified Testing:** Mock canonical transactions, not provider responses
- **Provider Independence:** Change providers without affecting domain logic

### Alternatives Considered

**Alternative 1: Store provider-specific formats**
- Pros: Preserves all original data
- Cons: Every service must handle multiple formats, coupling everywhere

**Alternative 2: Separate transaction models per chain**
- Pros: Preserves chain-specific details
- Cons: Domain services must handle multiple models, duplication

### Consequences

- **Positive:** Clean architecture, simplified domain logic
- **Negative:** Normalization layer required, potential data loss if canonical model incomplete

### Trade-offs

**Gain:** Maintainability, extensibility, testability  
**Lose:** Must ensure canonical model captures all necessary information

**Mitigation:** Store raw_provider_data (JSON) for debugging/edge cases

---

## ADR-003: PostgreSQL + Supabase as Database

**Status:** Accepted  
**Date:** 2026-09-22  
**Deciders:** System Architect, MASTER

### Context

LedgerLens requires a database for:
- Cases, wallets, transactions
- Entity registry
- Risk scores, patterns
- Evidence, notes, reports
- Strong relational model with complex queries

### Decision

Use **PostgreSQL 15+** as the database, hosted on **Supabase** for managed infrastructure.

### Rationale

**PostgreSQL Strengths:**
- Robust relational model with strong constraints
- JSONB support for flexible data (patterns, evidence)
- Recursive CTEs for graph queries
- Strong indexing (B-tree, GIN for JSON)
- Mature ecosystem, excellent Python support (SQLAlchemy)

**Supabase Strengths:**
- Managed PostgreSQL (no ops burden)
- Built-in auth, API generation
- Real-time subscriptions (future: live updates)
- Dashboard for database management
- Free tier for development/MVP

### Alternatives Considered

**Alternative 1: MongoDB**
- Pros: Flexible schema, good for JSON data
- Cons: Weak relational model, no foreign key enforcement, graph queries harder

**Alternative 2: Graph Database (Neo4j)**
- Pros: Native graph storage, powerful graph queries
- Cons: Poor relational model for cases/investigator data, additional complexity, overkill for MVP

**Alternative 3: Self-hosted PostgreSQL**
- Pros: Full control
- Cons: Ops burden (backups, scaling, monitoring), out of MVP scope

### Consequences

- **Positive:** Relational integrity, flexible JSON, managed infrastructure
- **Negative:** Supabase vendor dependency (mitigated: can export to any PostgreSQL)

### Trade-offs

**Gain:** Robust database, managed infrastructure, real-time features  
**Lose:** Vendor dependency (acceptable, PostgreSQL is portable)

---

## ADR-004: FastAPI as Backend Framework

**Status:** Accepted  
**Date:** 2026-09-22  
**Deciders:** System Architect, MASTER

### Context

Backend must provide REST API for frontend, orchestrate domain services, handle authentication, background jobs.

### Decision

Use **FastAPI** (Python) as the backend framework.

### Rationale

- **Modern async support:** Native async/await for blockchain API calls
- **Auto-generated OpenAPI docs:** Swagger UI out of the box
- **Pydantic validation:** Strong request/response schema validation
- **Type hints:** Python 3.10+ type safety
- **Python ecosystem:** Strong blockchain libraries (web3.py, tronpy)
- **Performance:** Comparable to Node.js/Go for I/O-bound workloads
- **AI/ML integration:** Easier Python LLM library integration (Phase 5)

### Alternatives Considered

**Alternative 1: Node.js + Express**
- Pros: JavaScript familiarity, large ecosystem
- Cons: Weaker blockchain library support, no native strong typing

**Alternative 2: Django + DRF**
- Pros: Mature, batteries-included
- Cons: More opinionated, slower than FastAPI, ORM coupling

**Alternative 3: Go**
- Pros: Performance, static typing
- Cons: Smaller blockchain ecosystem, longer development time, less AI/ML support

### Consequences

- **Positive:** Fast development, strong validation, async support, AI integration
- **Negative:** Python performance ceiling (acceptable for MVP I/O workload)

### Trade-offs

**Gain:** Developer productivity, ecosystem support, AI readiness  
**Lose:** Some runtime performance vs. compiled languages (not critical for MVP)

---

## ADR-005: React/Next.js + TypeScript for Frontend

**Status:** Accepted  
**Date:** 2026-09-22  
**Deciders:** System Architect, MASTER

### Context

Frontend must provide investigator dashboard, graph visualization, case management, evidence panel.

### Decision

Use **React** with **Next.js** framework and **TypeScript** for frontend.

### Rationale

- **Component-driven UI:** Reusable components for case cards, transaction lists, etc.
- **TypeScript:** Type safety, better IDE support, fewer runtime errors
- **Next.js:** SSR/SSG if needed, API routes, optimized production builds
- **Rich ecosystem:** Graph visualization libraries (react-force-graph, D3.js), UI libraries (shadcn, Tailwind)
- **Modern development:** Fast refresh, strong tooling

### Alternatives Considered

**Alternative 1: Vue.js**
- Pros: Simpler learning curve
- Cons: Smaller ecosystem for specialized libraries (graph viz)

**Alternative 2: Svelte**
- Pros: Excellent performance, simple syntax
- Cons: Smaller ecosystem, less mature tooling

**Alternative 3: Plain React (without Next.js)**
- Pros: Simpler setup
- Cons: Lose SSR, API routes, optimized builds

### Consequences

- **Positive:** Modern development experience, strong ecosystem, type safety
- **Negative:** Build complexity, bundle size (acceptable with optimization)

### Trade-offs

**Gain:** Developer productivity, type safety, ecosystem richness  
**Lose:** Some bundle size (mitigated with code splitting)

---

## ADR-006: Explainable Risk Scoring (Not ML Black-Box)

**Status:** Accepted  
**Date:** 2026-09-22  
**Deciders:** System Architect, MASTER

### Context

LedgerLens must provide risk scores for wallets. Investigators need to understand WHY a wallet is flagged.

### Decision

Implement **deterministic, explainable risk scoring** with versioned logic, not machine learning black-box models.

Risk scores must include:
- Total score (0-100)
- List of contributing factors with weights
- Evidence references for each factor
- Scoring version

Example:
```
Risk Score: 87/100

Factors:
+25 Known malicious association (Entity: ScamDB Record #4521)
+20 Rapid onward transfer (<2 hours)
+15 High fan-in (47 sources in 24h)
+12 Layering pattern (3-hop peel chain)
+10 Mixer interaction (Tornado Cash)
+05 Repeated case linkage (3 prior cases)
```

### Rationale

- **Explainability:** Investigators must understand and verify risk assessments
- **Trust:** Transparent logic builds trust in system
- **Auditability:** Scoring logic can be reviewed and challenged
- **Legal defensibility:** Risk scores may be used in investigations/court
- **Versioning:** Scoring logic can evolve while preserving historical context

### Alternatives Considered

**Alternative 1: ML-based risk scoring**
- Pros: Potentially more accurate with training data
- Cons: Black-box, hard to explain, requires training data, overkill for MVP

**Alternative 2: Simple rule-based flags (no scoring)**
- Pros: Very simple
- Cons: Less granular, harder to prioritize

### Consequences

- **Positive:** Trust, transparency, legal defensibility
- **Negative:** Requires careful factor design (acceptable, good design practice)

### Trade-offs

**Gain:** Explainability, trust, auditability  
**Lose:** Potential ML accuracy gains (not needed for MVP, can add ML as enhancement layer later)

---

## ADR-007: Alchemy as Primary Ethereum Provider

**Status:** Accepted  
**Date:** 2026-09-22  
**Deciders:** System Architect, MASTER

### Context

MVP requires Ethereum blockchain data. Multiple providers available: Alchemy, Infura, QuickNode, Etherscan.

### Decision

Use **Alchemy** as the primary Ethereum provider, with **Etherscan** as secondary/enrichment source.

### Rationale

**Alchemy:**
- Comprehensive API (transactions, token transfers, historical data)
- Generous free tier (300M compute units/month)
- Strong reliability and performance
- Good documentation
- Enhanced APIs (getAssetTransfers for easy token tracking)

**Etherscan (secondary):**
- Additional label data
- Fallback for rate limit scenarios
- Contract verification data
- Public watchlist data

### Alternatives Considered

**Alternative 1: Infura**
- Pros: Reliable, well-known
- Cons: Less generous free tier, fewer enhanced APIs

**Alternative 2: QuickNode**
- Pros: Performance, global CDN
- Cons: More expensive, less free tier

**Alternative 3: Self-hosted Ethereum node**
- Pros: Full control, no rate limits
- Cons: Infrastructure complexity, 2TB+ storage, out of MVP scope

### Consequences

- **Positive:** Reliable data access, generous free tier, good APIs
- **Negative:** Rate limits (mitigated with caching, fallback to Etherscan)

### Trade-offs

**Gain:** Reliable provider, good free tier, enhanced APIs  
**Lose:** Rate limit constraints (acceptable with architecture, can upgrade to paid tier)

---

## ADR-008: TronGrid for TRON Support (Phase 2+)

**Status:** Accepted  
**Date:** 2026-09-22  
**Deciders:** System Architect, MASTER

### Context

TRON is second priority blockchain (Phase 2+). TronGrid is official TRON network API.

### Decision

Use **TronGrid** as TRON blockchain provider. Defer implementation to Phase 2+, but architecture must support it.

### Rationale

- Official TRON Foundation API
- Free tier available
- Comprehensive transaction data
- Similar capabilities to Ethereum providers

### Alternatives Considered

**Alternative 1: Third-party TRON indexers**
- Pros: Potentially better APIs
- Cons: Less reliable, unofficial

**Alternative 2: Self-hosted TRON node**
- Cons: Infrastructure complexity, out of MVP scope

### Consequences

- **Positive:** Official provider, reliable
- **Negative:** Rate limits (same mitigation strategy as Ethereum)

### Trade-offs

**Gain:** Official support, reliability  
**Lose:** Rate limits (acceptable)

---

## ADR-009: Asynchronous Trace Jobs (Not Real-Time Streaming)

**Status:** Accepted  
**Date:** 2026-09-22  
**Deciders:** System Architect, MASTER

### Context

Multi-hop blockchain tracing can take significant time (seconds to minutes depending on depth, branch limits).

### Decision

Implement **asynchronous background jobs** for transaction tracing, not real-time WebSocket streaming or blocking API calls.

Flow:
1. Investigator submits case
2. API immediately returns case_id and job_id (202 Accepted)
3. Background worker fetches transactions, builds graph
4. Frontend polls job status or receives completion notification
5. Completed data displayed in dashboard

### Rationale

- **UX:** Frontend remains responsive
- **Scalability:** Background workers can scale independently
- **Reliability:** Job retries on provider failures
- **Provider rate limits:** Spread requests over time
- **Long-running operations:** Some traces may take minutes

### Alternatives Considered

**Alternative 1: Synchronous blocking API calls**
- Cons: Frontend hangs, poor UX, timeouts, single-threaded

**Alternative 2: Real-time WebSocket streaming**
- Pros: Live updates
- Cons: Complexity, overkill for MVP (can add in Phase 3+)

### Consequences

- **Positive:** Responsive UI, scalable architecture
- **Negative:** Requires job queue infrastructure (acceptable, standard pattern)

### Trade-offs

**Gain:** Scalability, responsiveness, reliability  
**Lose:** Not truly "real-time" (acceptable, async is fast enough)

---

## ADR-010: JWT Authentication (Not Session Cookies)

**Status:** Accepted  
**Date:** 2026-09-22  
**Deciders:** System Architect, MASTER

### Context

API requires authentication. Frontend and backend may be deployed separately (Vercel + Railway).

### Decision

Use **JWT (JSON Web Token) bearer authentication** with short-lived access tokens.

Flow:
1. Investigator logs in (POST /auth/login)
2. Backend returns JWT access token
3. Frontend stores token (localStorage or httpOnly cookie)
4. Frontend includes token in Authorization header for requests
5. Backend validates token signature and expiration

### Rationale

- **Stateless:** Backend doesn't need session storage
- **Scalable:** No session affinity required
- **Cross-origin:** Works with separate frontend/backend domains
- **Standard:** Industry-standard approach

### Alternatives Considered

**Alternative 1: Session cookies**
- Pros: Simpler (no token management)
- Cons: Session storage required, harder with separate domains

**Alternative 2: OAuth 2.0 with external provider**
- Pros: No password management
- Cons: Requires external provider, more complex, not needed for MVP

### Consequences

- **Positive:** Stateless, scalable, standard approach
- **Negative:** Token management (refresh tokens, expiration) required

### Trade-offs

**Gain:** Scalability, standard approach, cross-origin support  
**Lose:** Session simplicity (acceptable, JWT is well-understood)

---

## ADR-011: Progressive Agent Activation (Not All-At-Once)

**Status:** Accepted  
**Date:** 2026-09-22  
**Deciders:** MASTER, System Architect

### Context

LedgerLens has 12 specialist agent roles defined. Activating all agents simultaneously creates:
- Context consumption overhead
- Agent collision risk
- Duplicated reasoning
- Premature implementation

### Decision

Activate agents **progressively** according to actual development needs.

**Phase 0:** MASTER, System Architect, Documentation Engineer  
**Phase 1:** Database Engineer, Backend Engineer  
**Phase 2:** Blockchain Engineer, Graph Engineer  
**Phase 3:** Frontend Engineer, QA Engineer  
**Phase 4+:** Remaining specialists as needed

MASTER must evaluate necessity before activation:
1. Why is this agent needed now?
2. What task requires it?
3. What context does it need?
4. What does it own?
5. What agents does it depend on?

### Rationale

- **Efficiency:** Minimize unnecessary context consumption
- **Clarity:** Clear ownership boundaries
- **Quality:** Reduce agent collisions and conflicts
- **Coordination:** MASTER maintains integration control

### Alternatives Considered

**Alternative 1: Activate all agents at once**
- Cons: Context overhead, collisions, premature work

**Alternative 2: No specialist agents (MASTER does everything)**
- Cons: MASTER overwhelmed, no specialization

### Consequences

- **Positive:** Efficient context use, clear ownership, controlled pace
- **Negative:** Requires MASTER discipline to activate agents appropriately

### Trade-offs

**Gain:** Efficiency, clarity, control  
**Lose:** Must carefully plan agent activation (acceptable, good practice)

---

## ADR-012: Serial Execution Default (Not Parallel)

**Status:** Accepted  
**Date:** 2026-09-22  
**Deciders:** MASTER, System Architect

### Context

Multiple agents could work in parallel on independent tasks. But premature parallelization risks:
- Competing implementations
- Interface conflicts
- Integration complexity

### Decision

**Default mode:** Serial/controlled execution.

**Parallel execution allowed ONLY when:**
- Tasks are genuinely independent
- Ownership boundaries explicit
- Shared interfaces already defined
- No two agents modifying same files
- MASTER has verified integration risk is low

### Rationale

- **Safety:** Prevent architectural conflicts
- **Consistency:** Ensure interfaces designed before implementation
- **Quality:** MASTER reviews each phase before next
- **Coordination:** Single source of truth for integration

### Alternatives Considered

**Alternative 1: Parallel by default**
- Cons: Conflicts, duplicate work, integration failures

**Alternative 2: Strict serial always**
- Cons: Slower when safe parallelization possible

### Consequences

- **Positive:** Architectural consistency, fewer conflicts
- **Negative:** Potentially slower (acceptable, quality > speed)

### Trade-offs

**Gain:** Consistency, safety, integration control  
**Lose:** Some parallelization speed (acceptable trade-off)

---

## Summary of Key Decisions

| ADR | Decision | Status |
|-----|----------|--------|
| 001 | Provider-agnostic blockchain architecture | Accepted |
| 002 | Canonical transaction model | Accepted |
| 003 | PostgreSQL + Supabase | Accepted |
| 004 | FastAPI backend | Accepted |
| 005 | React/Next.js + TypeScript frontend | Accepted |
| 006 | Explainable risk scoring (not ML black-box) | Accepted |
| 007 | Alchemy as primary Ethereum provider | Accepted |
| 008 | TronGrid for TRON (Phase 2+) | Accepted |
| 009 | Asynchronous trace jobs | Accepted |
| 010 | JWT authentication | Accepted |
| 011 | Progressive agent activation | Accepted |
| 012 | Serial execution default | Accepted |
| 013 | Phase 1 closure (Case Foundation) | Accepted |

---

## Phase 1 Completion Record

### ADR-013: Phase 1 Closure — Case Foundation

**Status:** Accepted  
**Date:** 2026-09-23  
**Deciders:** MASTER / CTO

#### Context

Phase 1 (Case Foundation) required a verified database schema, migration, FastAPI case-management API, and passing tests before Phase 2 could be authorized. All structural, local, Supabase, migration, CRUD, and verification requirements have been met.

#### Decision

**Officially close Phase 1 as COMPLETE.**

#### Verification Evidence

| Layer | Result | Report |
|---|---|---|
| Structural / local code review | ✅ PASS | `docs/PHASE_1_VERIFICATION_REPORT.md` |
| Local tests + migration analysis | ✅ PASS (7/7) | `docs/PHASE_1_NON_SUPABASE_VERIFICATION.md` |
| Live Supabase migration + CRUD | ✅ PASS (100%) | `docs/PHASE_1_SUPABASE_VERIFICATION_REPORT.md` |
| Implementation report | ✅ COMPLETE | `docs/PHASE_1_REPORT.md` |

#### Supabase Verification Summary

- **Project:** `qeeljebpgonsvevwsjha` (ap-northeast-1, ACTIVE_HEALTHY, PostgreSQL 17.6)
- **Migration:** `migrations/001_initial_schema.sql` applied successfully
- **Schema:** `investigators` and `cases` tables, indexes, FKs, CHECK constraints, triggers (`trg_generate_case_number`, `trg_cases_updated_at`), and functions verified live
- **CRUD:** End-to-end case creation/retrieval/update verified; auto-generated `CASE-2026-000001`; `updated_at` trigger confirmed
- **Cleanup:** Temporary test case (`99d03bfc-2e96-4a48-a086-559d256da883`) and test investigator (`00000000-0000-0000-0000-000000000001`) deleted; post-cleanup row counts: `cases` = 0, `investigators` = 0

#### Security Confirmation

- No secrets, real credentials, or `.env` files committed — only `backend/.env.example` placeholders
- Temporary test data removed from live Supabase database

#### Consequences

- Phase 1 gate is CLOSED; Phase 2 (Blockchain Foundation) may proceed only upon explicit authorization
- Phase-2 agents (Blockchain Engineer, Graph/Intelligence Engineer) remain **inactive** until authorization
- Phase-1 schema is frozen — no modifications without a new decision record

#### Trade-offs

**Gain:** Verified foundation, clean checkpoint, auditable history  
**Lose:** None — closure records existing completed work only

---

**Document Status:** Updated through Phase 1 closure  
**Approval:** MASTER / CTO  
**Dependencies:** All Phase 1 verification reports
