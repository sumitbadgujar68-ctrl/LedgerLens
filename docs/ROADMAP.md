# LedgerLens Development Roadmap

**Last Updated:** 2026-09-25  
**Current Phase:** PHASE 6 — REPORTING (CLOSED ✅) — NEXT: PHASE 7 (NOT STARTED)  
**Status:** Phased Development Plan

---

## Overview

This roadmap defines the complete phased development plan for LedgerLens MVP, from foundation through hardening. Each phase has clear objectives, deliverables, acceptance criteria, and planned agent activations.

**Development Approach:** Progressive implementation with phase gates  
**Agent Activation:** Progressive, need-based  
**Execution Mode:** Serial by default, parallel when safe

---

## Phase Summary

| Phase | Name | Duration | Status | Agents |
|-------|------|----------|--------|--------|
| Phase 0 | Foundation | 2-3 days | CLOSED ✅ | MASTER, Architect, Documentation |
| Phase 1 | Case Foundation | 1 week | CLOSED ✅ | + Database, Backend |
| Phase 2 | Blockchain Foundation | 2 weeks | CLOSED ✅ | + Blockchain, Graph |
| Phase 3 | Investigation UI | 2 weeks | CLOSED ✅ | + Frontend, QA |
| Phase 4 | Intelligence | 2 weeks | Stages 1-3 COMPLETE, Stage 4 NOT STARTED | + VASP (Stage 3), Risk (Stage 4) |
| Phase 5 | AI Copilot | 1 week | CLOSED ✅ | + AI/Copilot |
| Phase 6 | Reporting | 1 week | CLOSED ✅ | Release support |
| Phase 7 | Hardening | 1 week | NOT STARTED | + Security |

**Total Estimated Duration:** 10-11 weeks (MVP)

---

## PHASE 0 — FOUNDATION

**Duration:** 2-3 days  
**Status:** CLOSED ✅ (Completed 2026-09-22)  
**Prerequisites:** None

### Objective

Establish project architecture, documentation, and coordination system before implementation begins.

### Active Agents

- MASTER / CTO (orchestration)
- System Architect (architecture design)
- Documentation / Context Engineer (project context)

### Deliverables

**Architecture:**
- [x] docs/ARCHITECTURE.md (system design, module boundaries)
- [x] docs/DOMAIN_MODEL.md (entities, relationships)
- [x] docs/API_CONTRACT.md (initial contracts)
- [x] docs/DATA_MODEL.md (conceptual database schema)
- [x] docs/DECISIONS.md (architectural decision records)

**Documentation:**
- [x] AGENTS.md (agent registry with activation tracking)
- [x] README.md (project overview)
- [x] docs/PROJECT_BRIEF.md (mission and scope)
- [x] docs/SECURITY_MODEL.md (security principles)
- [x] docs/TEAM_PROTOCOL.md (collaboration workflow)
- [x] docs/ROADMAP.md (this document)
- [x] docs/STATUS.md (current phase tracking)
- [ ] docs/KNOWN_LIMITATIONS.md (MVP scope boundaries)
- [x] tasks/TASK_BOARD.md (task tracking)

**Infrastructure:**
- [x] Git repository initialized
- [x] Directory structure established
- [x] .gitignore configured
- [ ] Development standards defined

### Acceptance Criteria

- [ ] All context documentation files exist and reviewed
- [ ] Agent team (3 agents) defined and documented
- [ ] Progressive activation policy documented
- [ ] Architecture boundaries clearly defined
- [ ] Development standards established
- [ ] No application features implemented
- [ ] Git repository clean and organized
- [ ] Ready for Phase 1 authorization

### Out of Scope

❌ No blockchain adapters  
❌ No database schemas  
❌ No API routes  
❌ No frontend components  
❌ No working code

**Phase 0 is documentation and architecture only.**

### Phase Gate

**STOP after Phase 0 verification. Await explicit Phase 1 authorization.**

---

## PHASE 1 — CASE FOUNDATION

**Duration:** 1 week  
**Status:** CLOSED ✅ (2026-09-23)  
**Prerequisites:** Phase 0 complete, Phase 1 authorization received

### Objective

Build foundational case management system with database persistence and basic backend API.

### New Agent Activations

- Database Engineer (database schema, migrations)
- Backend Engineer (FastAPI, API routes, services)

### Active Agents (Total: 5)

- MASTER / CTO
- System Architect (architectural guidance)
- Documentation Engineer (documentation updates)
- Database Engineer
- Backend Engineer

### Deliverables

**Database:**
- PostgreSQL schema design
- Supabase project setup
- Initial migration scripts
- Core tables:
  - `cases` (case_id, wallet_address, fraud_type, reported_amount, status, created_at)
  - `wallets` (wallet_id, case_id, address, blockchain, added_at)
  - `users` (user_id, email, password_hash, role)
- Row-level security (RLS) policies
- Indexes for common queries

**Backend:**
- FastAPI application structure
- Authentication system (JWT)
- API routes:
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/logout`
  - `POST /api/v1/cases` (create case)
  - `GET /api/v1/cases/{case_id}` (retrieve case)
  - `GET /api/v1/cases` (list cases)
  - `PUT /api/v1/cases/{case_id}` (update case)
- Pydantic models for request/response validation
- Database connection (SQLAlchemy + Supabase)
- Error handling
- Logging configuration
- Environment configuration

**Testing:**
- Unit tests for case service
- Integration tests for API endpoints
- Database migration tests

**Documentation:**
- API documentation (auto-generated Swagger/OpenAPI)
- Database schema documentation
- Setup instructions (README updates)

### Acceptance Criteria

**Functional:**
- [ ] Investigator can register/login
- [ ] Investigator can create a case with wallet address
- [ ] Investigator can retrieve case details
- [ ] Investigator can list their cases
- [ ] Case data persists in database
- [ ] Authentication works end-to-end

**Technical:**
- [ ] Database schema implemented and migrated
- [ ] API endpoints implemented and tested
- [ ] Authentication and authorization working
- [ ] Tests pass (unit + integration)
- [ ] API documentation generated
- [ ] Secrets management configured
- [ ] Logging works

**Quality:**
- [ ] Code reviewed by MASTER
- [ ] No secrets committed
- [ ] Error handling implemented
- [ ] Input validation working

### Out of Scope

❌ No blockchain integration yet  
❌ No transaction tracing  
❌ No graph generation  
❌ No frontend UI  
❌ No risk scoring  

**Phase 1 is case CRUD only.**

### Phase Gate

**STOP after Phase 1 verification. Await explicit Phase 2 authorization.**

---

## PHASE 2 — BLOCKCHAIN FOUNDATION

**Duration:** 2 weeks  
**Status:** CLOSED ✅ (2026-09-23)  
**Prerequisites:** Phase 1 complete, Phase 2 authorization received

### Objective

Implement blockchain data access, transaction normalization, multi-hop tracing, and graph generation.

### New Agent Activations

- Blockchain Engineer (blockchain adapters, providers)
- Graph / Intelligence Engineer (graph engine, traversal)

### Active Agents (Total: 7)

- MASTER / CTO
- System Architect
- Documentation Engineer
- Database Engineer (database updates)
- Backend Engineer (API updates)
- Blockchain Engineer
- Graph / Intelligence Engineer

### Deliverables

**Blockchain Adapter:**
- `BlockchainAdapter` interface (validate_address, fetch_transactions, etc.)
- `EthereumAdapter` implementation
- Provider abstraction layer
- `AlchemyProvider` implementation (Ethereum)
- `EtherscanProvider` implementation (secondary/enrichment)
- Transaction normalizer (provider response → canonical model)
- Error handling (timeouts, rate limits, provider failures)
- Retry logic with exponential backoff
- Caching for immutable blockchain data

**Database Schema Updates:**
- `transactions` table (canonical transaction model)
- `blockchain_providers` configuration table
- Indexes for transaction queries

**Transaction Tracing:**
- Multi-hop breadth-first traversal
- Configurable depth (1-10 hops)
- Branch limits (max outbound/inbound per wallet)
- Dust filtering (minimum amount threshold)
- Direction control (inbound, outbound, both)
- Time window filtering
- Background job architecture (Celery or FastAPI BackgroundTasks)

**Graph Engine:**
- Graph data structure (nodes: wallets, edges: transactions)
- Graph builder (from canonical transactions)
- Graph persistence (database storage strategy)
- Graph query interface

**API Updates:**
- `POST /api/v1/cases/{case_id}/trace` (initiate trace)
- `GET /api/v1/cases/{case_id}/trace/status` (job status)
- `GET /api/v1/cases/{case_id}/graph` (retrieve graph)
- `GET /api/v1/transactions/{tx_hash}` (transaction details)

**Testing:**
- Unit tests for adapters (mocked providers)
- Unit tests for normalizer
- Unit tests for graph engine
- Integration tests for trace workflow
- Test fixtures with known Ethereum addresses

**Documentation:**
- Blockchain adapter architecture
- Provider configuration guide
- Graph data model

### Acceptance Criteria

**Functional:**
- [ ] System can validate Ethereum address
- [ ] System can fetch Ethereum transaction history (via Alchemy)
- [ ] System normalizes Ethereum transactions to canonical model
- [ ] System stores transactions in database
- [ ] System builds transaction graph
- [ ] System performs multi-hop trace (configurable depth)
- [ ] System handles provider failures gracefully
- [ ] Background jobs work asynchronously

**Technical:**
- [ ] Adapter interface defined and implemented
- [ ] Provider abstraction working
- [ ] Transaction normalization working
- [ ] Graph generation working
- [ ] Caching implemented
- [ ] Rate limit handling implemented
- [ ] Tests pass
- [ ] No API keys exposed

**Quality:**
- [ ] Provider-agnostic design verified
- [ ] Canonical transaction model verified
- [ ] Error states properly handled
- [ ] Code reviewed by MASTER

### Out of Scope

❌ TRON support (Phase 2+, if needed)  
❌ Pattern detection (Phase 4)  
❌ VASP attribution (Phase 4)  
❌ Risk scoring (Phase 4)  
❌ Frontend UI (Phase 3)  

**Phase 2 is blockchain foundation only.**

### Phase Gate

**STOP after Phase 2 verification. Await explicit Phase 3 authorization.**

---

## PHASE 3 — INVESTIGATION UI

**Duration:** 2 weeks  
**Status:** CLOSED ✅ (2026-09-23)  
**Prerequisites:** Phase 2 complete, Phase 3 authorization received

### Objective

Build investigator-facing web application with dashboard, case management, graph visualization, and evidence panel.

### New Agent Activations

- Frontend Engineer (React/Next.js UI)
- QA / Test Engineer (end-to-end testing)

### Active Agents (Total: 9)

- MASTER / CTO
- System Architect
- Documentation Engineer
- Database Engineer (as needed)
- Backend Engineer (API refinements)
- Blockchain Engineer (as needed)
- Graph Engineer (as needed)
- Frontend Engineer
- QA Engineer

### Deliverables

**Frontend Application:**
- Next.js project setup
- TypeScript configuration
- Tailwind CSS styling
- Authentication UI (login, logout)
- Dashboard (case list, case cards)
- Case intake form (wallet address, fraud type, amount)
- Case detail page
- Transaction graph visualization (react-force-graph or similar)
- Transaction list/table
- Transaction detail modal
- Evidence panel (pin transactions, add notes)
- Loading states
- Error states
- API client (axios or fetch)

**Components:**
- `<LoginForm />`
- `<Dashboard />`
- `<CaseCard />`
- `<CaseIntakeForm />`
- `<CaseDetail />`
- `<TransactionGraph />`
- `<TransactionList />`
- `<TransactionDetail />`
- `<EvidencePanel />`
- `<NoteEditor />`

**State Management:**
- React Context or Zustand for global state
- Authentication state
- Case state
- Graph state

**API Integration:**
- Authentication flow
- Case CRUD
- Trace initiation
- Graph retrieval
- Transaction retrieval

**Testing:**
- Component unit tests (Jest, React Testing Library)
- End-to-end tests (Playwright or Cypress)
- Visual regression tests (optional)

**Documentation:**
- Frontend architecture
- Component documentation
- Setup instructions

### Acceptance Criteria

**Functional:**
- [ ] Investigator can login via UI
- [ ] Investigator can create case via UI
- [ ] Investigator can view case dashboard
- [ ] Investigator can initiate trace via UI
- [ ] Investigator sees trace progress indicator
- [ ] Investigator can view transaction graph (interactive)
- [ ] Investigator can click wallet/transaction for details
- [ ] Investigator can pin transactions as evidence
- [ ] Investigator can add notes to case
- [ ] UI handles loading states gracefully
- [ ] UI displays errors clearly

**Technical:**
- [ ] Frontend connects to backend API
- [ ] Authentication flow works end-to-end
- [ ] Graph visualization renders correctly
- [ ] Responsive design (desktop focus, mobile acceptable)
- [ ] TypeScript types aligned with API contracts
- [ ] Tests pass
- [ ] No API keys in frontend code

**Quality:**
- [ ] UI reviewed by MASTER
- [ ] UX flows tested
- [ ] Error messages helpful
- [ ] Loading states present
- [ ] Accessibility basics (semantic HTML, alt text)

### Out of Scope

❌ Pattern detection visualization (Phase 4)  
❌ Risk score display (Phase 4)  
❌ VASP attribution display (Phase 4)  
❌ AI copilot UI (Phase 5)  
❌ Report generation UI (Phase 6)  

**Phase 3 is investigation UI foundation.**

### Phase Gate

**STOP after Phase 3 verification. Await explicit Phase 4 authorization.**

---

## PHASE 4 — INTELLIGENCE

**Duration:** 2 weeks  
**Status:** Stages 1-3 COMPLETE, Stage 4 (Risk Engine) NOT STARTED  
**Prerequisites:** Phase 3 complete, Phase 4 authorization received

### Objective

Implement pattern detection, entity/address intelligence, VASP attribution, and explainable risk scoring.

### New Agent Activations

- VASP / Entity Intelligence Engineer (entity registry, attribution) — **ACTIVATED for Stage 3, now DEACTIVATED**
- Risk Engineer (risk scoring engine) — **NOT YET ACTIVATED (Stage 4)**

### Active Agents (Total: 11, with Stage 3 agents now DEACTIVATED)

- MASTER / CTO
- System Architect
- Documentation Engineer
- Database Engineer (schema updates)
- Backend Engineer (API updates)
- Blockchain Engineer (as needed)
- Graph Engineer (pattern detection integration)
- Frontend Engineer (intelligence UI) — **NOT YET ACTIVATED (Stage 4)**
- QA Engineer
- VASP / Entity Intelligence Engineer — **ACTIVATED for Stage 3, now DEACTIVATED**
- Risk Engineer — **NOT YET ACTIVATED (Stage 4)**

### Stage Completion Status

- **Stage 1 — Database Foundation:** ✅ COMPLETE (migrations 003, entities/patterns/vasp_attributions/risk_scores tables, seed catalog)
- **Stage 2 — Pattern Detection Engine:** ✅ COMPLETE (7 deterministic detectors, persistence service, comprehensive tests)
- **Stage 3 — Entity Intelligence + VASP Attribution:** ✅ COMPLETE (address registry, attribution engine with DIRECT/SUPPORTED/INFERRED/UNKNOWN provenance levels)
- **Stage 4 — Explainable Risk Engine:** NOT STARTED (requires Risk Engineer activation)

### Deliverables

**Pattern Engine (Stage 2 — COMPLETE):**
- Pattern detection algorithms:
  - Peel chain detection
  - Rapid forwarding (<2 hours)
  - High fan-in (>N sources in timeframe)
  - High fan-out (>N destinations in timeframe)
  - Layering detection
  - Consolidation patterns
  - Split-and-forward patterns
  - Mixer interaction detection
  - Bridge interaction detection
- Pattern storage (database)
- Pattern API endpoints

**Entity / Address Intelligence (Stage 3 — COMPLETE):**
- Entity registry schema
- Entity types (exchange, vasp, mixer, bridge, protocol, scam, unknown)
- Known entity database (curated):
  - Major exchanges (Binance, Coinbase, Kraken, etc.)
  - Known mixers (Tornado Cash, etc.)
  - Known bridges (if applicable)
  - Demo scam addresses
- Entity lookup service
- Entity clustering (basic)
- Entity API endpoints

**VASP Attribution (Stage 3 — COMPLETE):**
- VASP matcher service
- Matching strategies:
  - Exact address match
  - Cluster match
  - Behavioral similarity
  - Historical transaction patterns
- Confidence calculation
- Evidence aggregation
- Attribution API endpoints

**Risk Engine (Stage 4 — NOT STARTED):**
- Risk scoring framework
- Risk factors:
  - Known malicious association (+25)
  - Rapid onward transfer (+20)
  - High fan-in (+15)
  - Layering pattern (+12)
  - Mixer interaction (+10)
  - Repeated case linkage (+5)
  - (Weights configurable)
- Risk score calculation
- Risk explanation generation
- Risk versioning
- Risk API endpoints

**Database Schema Updates (Stage 1 — COMPLETE):**
- `entities` table
- `entity_addresses` table
- `patterns` table
- `vasp_attributions` table
- `risk_scores` table
- `risk_factors` table

**API Updates:**
- `GET /api/v1/cases/{case_id}/patterns` (Stage 2)
- `GET /api/v1/entities/{entity_id}` (Stage 3)
- `GET /api/v1/addresses/{address}/entity` (Stage 3)
- `GET /api/v1/cases/{case_id}/attributions` (Stage 3)
- `GET /api/v1/wallets/{wallet_id}/risk` (Stage 4 — NOT STARTED)
- `GET /api/v1/risk/{risk_id}/explanation` (Stage 4 — NOT STARTED)

**Frontend Updates (Stage 4 — NOT STARTED):**
- Pattern badges in graph visualization
- VASP attribution display (with confidence)
- Risk score display (with factor breakdown)
- Evidence links to risk factors
- Entity detail modal

**Testing:**
- Unit tests for pattern detection (Stage 2 — COMPLETE)
- Unit tests for VASP matcher (Stage 3 — COMPLETE)
- Unit tests for risk engine (Stage 4 — NOT STARTED)
- Integration tests for intelligence APIs
- End-to-end intelligence workflow tests

**Documentation:**
- Pattern detection methodology (Stage 2)
- Entity registry structure (Stage 3)
- VASP attribution methodology (Stage 3)
- Risk scoring documentation (Stage 4)

### Acceptance Criteria

**Functional:**
- [x] System detects patterns in transaction graph (Stage 2)
- [x] System identifies known entities from registry (Stage 3)
- [x] System attributes destinations to VASPs with confidence (Stage 3)
- [ ] System calculates explainable risk scores (Stage 4)

**Technical:**
- [x] Pattern detection working (Stage 2)
- [x] Entity registry populated with demo data (Stage 3)
- [x] VASP matcher working (Stage 3)
- [ ] Risk engine producing explainable scores (Stage 4)

**Quality:**
- [ ] Explainability verified
- [ ] No black-box scores
- [ ] Confidence scores accurate
- [ ] Human-in-the-loop language used
- [ ] Code reviewed by MASTER

### Out of Scope

❌ AI/LLM integration (Phase 5)  
❌ Report generation (Phase 6)  
❌ Advanced clustering algorithms  
❌ Real-time pattern detection  

**Phase 4 is intelligence foundation. Stages 1-3 complete. Stage 4 pending.**

### Phase Gate

**STOP after Phase 4 Stage 4 verification. Await explicit Phase 5 authorization.**

---

## PHASE 5 — AI COPILOT

**Duration:** 1 week  
**Status:** CLOSED ✅ (2026-09-24) — backend service, API, 74-test suite (12/12 acceptance categories), 190/190 full backend suite  
**Documented limitation:** real LLM/provider behavior UNVERIFIED — no `OPENAI_API_KEY` configured; provider mocked in tests  
**Prerequisites:** Phase 4 complete ✅, Phase 5 authorization received ✅

### Objective

Implement LLM-based investigation assistant grounded in case data for natural language Q&A, explanations, and summaries.

### New Agent Activations

- AI / Copilot Engineer (LLM integration, prompting)

### Active Agents (Total: 12)

- MASTER / CTO
- System Architect
- Documentation Engineer
- Database Engineer (as needed)
- Backend Engineer (copilot API)
- Blockchain Engineer (as needed)
- Graph Engineer (as needed)
- Frontend Engineer (copilot UI)
- QA Engineer
- VASP Engineer (as needed)
- Risk Engineer (as needed)
- AI / Copilot Engineer

### Deliverables

**AI Copilot Service:**
- LLM integration (OpenAI GPT-4 or similar)
- Prompt engineering for investigation assistant
- Grounding layer (case data retrieval)
- Tool/function calling for structured data access
- Context window management
- Response citation (link to source data)
- Hallucination prevention
- Copilot service layer

**Capabilities:**
- Answer investigator questions:
  - "Why is this wallet suspicious?"
  - "What are the major fund paths?"
  - "Which wallet received funds from the most case-linked addresses?"
  - "How many hops reached the candidate VASP?"
  - "Which transactions deserve preservation?"
- Summarize case investigation
- Explain risk score
- Explain patterns
- Suggest next investigative steps

**API Updates:**
- `POST /api/v1/copilot/ask` (ask question about case)
- `POST /api/v1/copilot/summarize` (summarize case)
- `POST /api/v1/copilot/explain_risk` (explain risk score)

**Frontend Updates:**
- Copilot chat interface
- Chat history
- Question suggestions
- Loading indicator (LLM response)
- Citation links (click to view source data)

**Testing:**
- Unit tests for grounding layer
- Integration tests for copilot service
- End-to-end copilot workflow tests
- Hallucination tests (ensure no fabricated data)

**Documentation:**
- Copilot architecture
- Prompt engineering guide
- Grounding methodology
- Safety constraints

### Acceptance Criteria

**Functional:**
- [ ] Investigator can ask questions via chat UI
- [ ] Copilot answers questions grounded in case data
- [ ] Copilot cites sources (transactions, entities, etc.)
- [ ] Copilot summarizes case investigation
- [ ] Copilot explains risk scores
- [ ] Copilot does NOT fabricate evidence
- [ ] Copilot responds "insufficient data" when appropriate

**Technical:**
- [ ] LLM integration working
- [ ] Grounding layer retrieves correct case data
- [ ] Responses include citations
- [ ] Context window managed efficiently
- [ ] Tests pass (including no-hallucination tests)

**Safety:**
- [ ] No hallucinated transaction hashes
- [ ] No hallucinated entities
- [ ] No hallucinated risk scores
- [ ] Explicit uncertainty when data unavailable

**Quality:**
- [ ] Copilot reviewed by MASTER
- [ ] Prompt engineering reviewed
- [ ] Safety constraints verified

### Out of Scope

❌ Autonomous investigation (human-in-the-loop always)  
❌ Legal conclusions  
❌ Training custom models  

**Phase 5 is AI assistance only.**

### Phase Gate

**STOP after Phase 5 verification. Await explicit Phase 6 authorization.**

---

## PHASE 6 — REPORTING

**Duration:** 1 week  
**Status:** CLOSED ✅ (Completed 2026-09-25 — MASTER / CTO checkpoint)  
**Prerequisites:** Phase 5 complete, Phase 6 authorization received

### Objective

Implement investigation report generation with evidence aggregation, PDF export, and structured output.

### New Agent Activations

None (existing agents sufficient, Release Engineer support if needed)

### Active Agents

- MASTER / CTO
- Backend Engineer (report service)
- Frontend Engineer (report UI)
- QA Engineer
- Documentation Engineer (report template)

### Deliverables

**Report Generation Service:**
- Report aggregation logic
- Report sections:
  - Case information
  - Initial reported wallet
  - Investigation methodology
  - Transaction timeline
  - Graph summary (key metrics)
  - Intermediary wallets
  - Destination entities
  - VASP attribution results
  - Risk analysis
  - Detected patterns
  - Evidence references
  - Investigator notes
  - Limitations and disclaimers
  - Generated timestamp
- Report templating (HTML, JSON, PDF)
- PDF generation (WeasyPrint or similar)
- Report sanitization (prevent XSS in HTML reports)

**Evidence Management:**
- Evidence pinning enhancements
- Note categorization
- Evidence tagging
- Evidence export

**API Updates:**
- `POST /api/v1/cases/{case_id}/reports` (generate report)
- `GET /api/v1/reports/{report_id}` (retrieve report metadata)
- `GET /api/v1/reports/{report_id}/download` (download PDF/JSON/HTML)

**Frontend Updates:**
- Report generation UI
- Report preview
- Report download button
- Report format selector (PDF, JSON, HTML)

**Testing:**
- Unit tests for report generator
- Integration tests for report API
- End-to-end report generation tests
- PDF generation tests

**Documentation:**
- Report structure documentation
- Report template guide

### Acceptance Criteria

**Functional:**
- [x] Investigator can generate report from case
- [x] Report includes all case data
- [x] Report includes graph summary
- [x] Report includes VASP attributions
- [x] Report includes risk analysis
- [x] Report includes evidence and notes
- [x] Report includes limitations section
- [x] Investigator can download report as PDF
- [x] Investigator can download report as JSON

**Technical:**
- [x] Report generation working
- [x] PDF export working — via the approved renderer path (`reportlab`); when no renderer is installed the export fails explicitly with `PDF_RENDERER_UNAVAILABLE` and **never** returns fake PDF bytes
- [x] Report sanitization implemented (all HTML output escaped; strict CSP; no executable markup)
- [x] Tests pass

**Quality:**
- [x] Reports reviewed for completeness
- [x] Reports reviewed for clarity
- [x] Disclaimers present
- [x] No fabricated data in reports

### Out of Scope

❌ Automated report scheduling  
❌ Report sharing/collaboration  
❌ Multi-case comparison reports  

**Phase 6 is basic reporting.**

### Phase 6 Closure Record

**Closed:** 2026-09-25 by MASTER / CTO (final checkpoint commit)

**Delivered (Steps 1–6):**
- [x] Report aggregation service covering all 14 documented sections (`backend/app/services/reporting/generator.py`)
- [x] Evidence aggregation with chain-of-custody provenance (Step 2)
- [x] Report schemas, `reports`/`jobs` models, deterministic persistence (Step 3)
- [x] Report API: `POST /cases/{id}/reports`, `GET /cases/{id}/reports`, `GET /reports/{id}/download` (Step 4)
- [x] Report templating: sanitized HTML, deterministic JSON, PDF export (Step 5)
- [x] Artifact storage + download without regeneration (`reports.file_path`)
- [x] Report sanitization (XSS) tests
- [x] Migrations `004_phase6_evidence.sql` and `005_phase6_reports_jobs.sql` prepared with rollbacks

**Verification at closure:**
- Phase 6 focused report suite: **78/78 PASS** (`test_report_aggregation`, `test_report_persistence`, `test_report_api`, `test_report_rendering`)
- Step 5 export-rendering suite: **37/37 PASS**
- Complete backend suite: **268/268 PASS**
- Frontend suite: **9/9 PASS**; production build PASS (no regressions)
- Secrets scan: CLEAN

**Documented limitations / deferrals:**
- PDF rendering uses the approved renderer path (`reportlab==5.0.1`). If no renderer library is installed, export fails explicitly with `PDF_RENDERER_UNAVAILABLE` and no PDF artifact is persisted — an unavailable renderer is never reported as a successful export.
- Migrations 004/005 are **prepared but not yet applied to the live database** (connectivity unavailable at closure); apply when connectivity is restored.
- Phase 6 **frontend report UI** (report generation UI, preview, download button, format selector) was explicitly excluded from the Phase 6 step authorization and remains deferred.

### Phase Gate

**Phase 6 CLOSED ✅. STOP. Await explicit Phase 7 authorization — do NOT start Phase 7.**

---

## PHASE 7 — HARDENING

**Duration:** 1 week  
**Status:** Not Started  
**Prerequisites:** Phase 6 complete, Phase 7 authorization received

### Objective

Security audit, performance testing, regression testing, bug fixes, deployment preparation, final documentation.

### New Agent Activations

- Security Engineer (security audit)

### Active Agents

- MASTER / CTO (final review)
- Security Engineer
- QA Engineer (regression testing)
- All other agents (bug fixes as needed)

### Deliverables

**Security Audit:**
- Secrets management review
- Authentication/authorization review
- Input validation review
- API security review
- Dependency vulnerability scan
- OWASP Top 10 checklist
- Security issues remediation

**Performance Testing:**
- Load testing (API endpoints)
- Blockchain API rate limit testing
- Database query optimization
- Graph generation performance
- Background job performance
- Caching effectiveness

**Regression Testing:**
- Full end-to-end test suite
- All features tested
- Edge cases verified
- Error scenarios tested

**Bug Fixes:**
- Critical bugs fixed
- High-priority bugs fixed
- Known issues documented (if deferring)

**Deployment Preparation:**
- Production environment setup
- Environment variable configuration
- Database migration plan
- Deployment documentation
- Rollback procedure
- Monitoring setup

**Documentation:**
- User guide (investigator manual)
- Setup/installation guide
- API documentation finalized
- Architecture documentation finalized
- Known limitations documented
- Troubleshooting guide

### Acceptance Criteria

**Security:**
- [ ] Security audit complete
- [ ] Critical vulnerabilities remediated
- [ ] Secrets management verified
- [ ] No hardcoded credentials

**Performance:**
- [ ] API response times acceptable (<2s standard requests)
- [ ] Graph generation performant (reasonable hops)
- [ ] Database queries optimized
- [ ] Caching working

**Quality:**
- [ ] All tests pass
- [ ] Regression testing complete
- [ ] Critical bugs fixed
- [ ] Known issues documented

**Deployment:**
- [ ] Production environment ready
- [ ] Deployment documentation complete
- [ ] Monitoring configured
- [ ] Rollback plan documented

**Documentation:**
- [ ] User guide complete
- [ ] Setup guide complete
- [ ] API docs complete
- [ ] Architecture docs final

### MVP Completion

**MVP is ready when:**
- [ ] All Phase 0-7 deliverables complete
- [ ] All acceptance criteria met
- [ ] Security audit passed
- [ ] Performance acceptable
- [ ] Documentation complete
- [ ] Deployment ready

---

## Agent Activation Schedule

| Phase | New Activations | Total Active |
|-------|-----------------|--------------|
| Phase 0 | MASTER, Architect, Documentation | 3 |
| Phase 1 | Database, Backend | 5 |
| Phase 2 | Blockchain, Graph | 7 |
| Phase 3 | Frontend, QA | 9 |
| Phase 4 | VASP, Risk | 11 |
| Phase 5 | AI/Copilot | 12 |
| Phase 6 | (existing agents) | 12 |
| Phase 7 | Security | 13 |

---

## Post-MVP Enhancements

**Future Phases (Not MVP):**

### Phase 8 — Multi-Chain Expansion
- TRON adapter implementation
- Solana adapter implementation
- Bitcoin adapter implementation
- Cross-chain tracing

### Phase 9 — Advanced Intelligence
- Advanced clustering algorithms
- DeFi protocol integration
- Bridge tracking
- Mixer pattern enhancements

### Phase 10 — Collaboration Features
- Multi-investigator collaboration
- Case sharing
- Team workspaces
- Audit logs

### Phase 11 — Authorized Integrations
- External intelligence sources (if authorized)
- LEA system integration (if authorized)
- Exchange partnerships (if authorized)

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Provider rate limits | Caching, multiple providers, rate limit monitoring |
| Scope creep | Strict phase gates, MASTER approval required |
| Agent conflicts | Serial execution default, clear ownership |
| Security vulnerabilities | Security review at each phase, Phase 7 audit |
| Performance issues | Performance testing in Phase 7 |
| Attribution uncertainty | Confidence scores, evidence chains, disclaimers |

---

## Success Metrics

**MVP Success:**
- Investigator can trace funds from victim-reported wallet
- Investigator sees transaction graph
- Investigator sees VASP attribution with confidence
- Investigator understands why wallet is suspicious (explainable)
- Investigator can generate investigation report
- System handles provider failures gracefully

**MVP is NOT:**
- Commercial Chainalysis replacement
- Legally definitive attribution
- Real-time mempool monitoring
- All-blockchain support

**MVP IS:**
- Credible blockchain intelligence workstation
- Explainable investigation tool
- Human-in-the-loop workflow
- Foundation for future enhancement

---

## Roadmap Status

**Last Updated:** 2026-09-25  
**Current Phase:** Phase 6 — Reporting (CLOSED ✅ 2026-09-25)  
**Next Phase:** Phase 7 — Hardening (NOT STARTED)

**Phase 0 Completion Target:** 2026-09-24 (met 2026-09-22)  
**MVP Completion Target:** 2026-12-01 (approximate)

---

**Document Status:** Complete phased development roadmap  
**Approval Required:** MASTER / CTO  
**Dependencies:** ARCHITECTURE.md, TEAM_PROTOCOL.md, STATUS.md
