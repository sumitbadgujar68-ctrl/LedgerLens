# LedgerLens Agent Registry

**Last Updated:** 2026-09-25  
**Current Phase:** PHASE 7 — HARDENING (IN PROGRESS ✅)  
**Previous Phase:** PHASE 6 — REPORTING (CLOSED ✅)  
**Phase 7 Authorization:** Granted by MASTER / CTO — 2026-09-25

## Purpose

This file tracks the OpenCode agent team structure, activation status, and ownership boundaries for the LedgerLens project.

## Progressive Agent Activation Policy

The LedgerLens team follows a **progressive agent activation** strategy:

- Agents are activated **only when needed** for current phase work
- Agents are **NOT created merely because their role exists** in the long-term team specification
- The MASTER evaluates necessity before every agent activation
- Parallel agent execution requires explicit ownership boundaries, stable interfaces, and MASTER approval
- Serial/controlled execution is the default mode

## Current Standing Active Agents (Phase 7 — IN PROGRESS)

**Phase 7 note:** Phase 7 was authorized by MASTER / CTO on 2026-09-25. Per the progressive activation policy, specialists are activated one task at a time: the **Security Engineer** (TASK-P7-001/002) and, since 2026-09-25, the **QA / Test Engineer** (TASK-P7-003) are active. Release / Documentation Engineer and owning engineers remain on standby until their Phase 7 tasks begin.

### MASTER / CTO (ACTIVE)
**Status:** Active  
**Activated:** 2026-09-22  
**Responsibilities:**
- Overall orchestration
- Cross-cutting verification
- Integration decisions
- Status tracking
- Phase gate management
- Agent activation decisions

**Ownership:**
- Project-wide coordination
- AGENTS.md (this file)
- Phase gate enforcement

---

### SECURITY ENGINEER (ACTIVE — Phase 7)
**Status:** Active  
**Activated:** 2026-09-25  
**Agent definition:** `.opencode/agents/security.md`  
**Responsibilities:**
- Security audit of backend, frontend, database, migrations and configuration
- OWASP Top 10 mapping and dependency-scan assessment
- Findings register with severity, `file:line` evidence and owners
- Security testing requirements per `SECURITY_MODEL.md` §17.1
- Remediation planning (fixes applied by owning agents)

**Ownership:**
- `docs/PHASE_7_SECURITY_AUDIT.md`
- `backend/tests/test_security*.py`
- Findings/reports only for files owned by other agents

---

### QA / TEST ENGINEER (ACTIVE — Phase 7)
**Status:** Active  
**Activated:** 2026-09-25 (TASK-P7-003; previously activated 2026-09-23 for Phase 3)  
**Agent definition:** `.opencode/agents/qa.md`  
**Responsibilities:**
- Full regression execution (backend pytest, frontend vitest, lint, production build)
- Edge-case and error-scenario coverage for Phase 6/7 paths (`SECURITY_MODEL.md` §17.1, audit §8)
- Coverage verification, or a documented verification gap when tooling is unavailable
- Regression report with exact counts from actual runs
- Working-tree verification before any checkpoint

**Ownership:**
- `backend/tests/**` (regression suites; new edge/error tests)
- `frontend/src/__tests__/**`, `frontend/tests/**`
- `docs/PHASE_7_REGRESSION_REPORT.md`
- `AGENTS.md` / `docs/STATUS.md` / `tasks/TASK_BOARD.md` — status lines only for this activation

---

### AI / COPILOT ENGINEER (DEACTIVATED — Phase 5 CLOSED)
**Status:** Deactivated — 2026-09-24 (post Phase-5 checkpoint)  
**Activated:** 2026-09-24  
**Deactivated:** 2026-09-24  
**Responsibilities:**
- AI Copilot service: `backend/app/services/ai/`
- Grounding, tools, context, citations, safety layers
- Copilot orchestration engine
- Copilot API endpoints: `backend/app/api/v1/copilot.py`
- Copilot schemas: `backend/app/models/copilot_schemas.py`
- Phase 5 tests: `backend/tests/test_copilot.py`

**Ownership:**
- backend/app/services/ai/
- backend/app/api/v1/copilot.py
- backend/app/models/copilot_schemas.py
- backend/tests/test_copilot.py

---

### VASP / ENTITY INTELLIGENCE ENGINEER (DEACTIVATED — Phase 4 Stage 3 Complete)
**Status:** Deactivated — 2026-09-23 (post Stage 3 checkpoint)  
**Activated:** 2026-09-23 (Phase 4 Stage 3 — Entity Intelligence)  
**Deactivated:** 2026-09-23  
**Responsibilities:**
- Entity Intelligence: `backend/app/services/entity/`
- Address Registry: `backend/app/services/entity/address_registry.py`
- Attribution Engine: `backend/app/services/entity/attribution_engine.py`
- VASP attribution service
- Unit tests for entity lookup and attribution

**Ownership:**
- backend/app/services/entity/

---

### RISK ENGINEER (DEACTIVATED — Phase 4 Stage 4 Complete)
**Status:** Deactivated — 2026-09-24 (post Stage 4 checkpoint)  
**Activated:** 2026-09-24 (Phase 4 Stage 4 — Explainable Risk Engine)  
**Deactivated:** 2026-09-24  
**Responsibilities:**
- Risk Engine: `backend/app/services/risk/`
- Factor calculators: `backend/app/services/risk/factors.py`
- Risk engine orchestrator: `backend/app/services/risk/engine.py`
- Risk explanations: `backend/app/services/risk/explanation.py`
- Risk API: `backend/app/api/v1/risk.py`
- Unit tests for risk factors, engine, and API

**Ownership:**
- backend/app/services/risk/
- backend/app/api/v1/risk.py

---

### PHASE 3 AGENTS (DEACTIVATED after Phase-3 verification gate)

#### FRONTEND ENGINEER (DEACTIVATED)
**Status:** Deactivated — 2026-09-23 (post Phase-3 verification)  
**Activated:** 2026-09-23  
**Deactivated:** 2026-09-23  
**Responsibilities:**
- React 18 + TypeScript + Tailwind CSS application implementation
- React Flow fund-flow graph visualization
- Investigation workspace, dashboard, case creation, inspector drawers
- TanStack Query API integration with FastAPI backend
- Dark forensic UX aesthetic & accessibility standards
- Client state management (Zustand)

**Ownership:**
- frontend/

---

#### QA / TEST ENGINEER (DEACTIVATED)
**Status:** Deactivated — 2026-09-23 (post Phase-3 verification)  
**Activated:** 2026-09-23  
**Deactivated:** 2026-09-23  
**Responsibilities:**
- Frontend unit and integration tests (Vitest + Testing Library)
- End-to-end user flow verification
- API error state & boundary validation

**Ownership:**
- frontend/src/__tests__/
- frontend/tests/
- backend/tests/ (regression suite maintenance)

---

### STANDING ROLES / SPECIALISTS ON STANDBY

### SYSTEM ARCHITECT (STANDBY)
**Status:** Standby  
**Activated:** 2026-09-22  
**Responsibilities:**
- Architecture design
- Module boundaries
- Service contracts
- Architectural Decision Records (ADRs)

**Ownership:**
- docs/ARCHITECTURE.md
- docs/DOMAIN_MODEL.md
- docs/API_CONTRACT.md
- docs/DATA_MODEL.md
- docs/DECISIONS.md

---

### DOCUMENTATION / CONTEXT ENGINEER (STANDBY)
**Status:** Standby  
**Activated:** 2026-09-22  
**Responsibilities:**
- Project memory maintenance
- Context file updates

**Ownership:**
- README.md
- docs/PROJECT_BRIEF.md
- docs/SECURITY_MODEL.md
- docs/TEAM_PROTOCOL.md
- docs/ROADMAP.md
- docs/STATUS.md
- tasks/TASK_BOARD.md

---

### DATABASE ENGINEER (STANDBY — Phase-2 engagement closed)
**Status:** Standby; Phase-2 schema extension engagement closed 2026-09-23  
**Activated:** 2026-09-22  
**Ownership:**
- database/
- migrations/

---

### BACKEND ENGINEER (STANDBY — Phase-1/2 delivered)
**Status:** Standby  
**Activated:** 2026-09-22  
**Ownership:**
- backend/

---

### PHASE 2 AGENTS (DEACTIVATED after checkpoint)

#### BLOCKCHAIN ENGINEER (DEACTIVATED)
**Status:** Deactivated — 2026-09-23 (post Phase-2 checkpoint)  
**Activated:** 2026-09-23  
**Deactivated:** 2026-09-23  
**Ownership:**
- backend/app/services/blockchain/

---

#### GRAPH / INTELLIGENCE ENGINEER (DEACTIVATED)
**Status:** Deactivated — 2026-09-23 (post Phase-2 checkpoint)  
**Activated:** 2026-09-23  
**Deactivated:** 2026-09-23  
**Ownership:**
- backend/app/services/graph/
- backend/app/services/tracing/

---

## Planned Future Agents (Not Yet Active)

### PHASE 5 AGENTS

#### AI / COPILOT ENGINEER
**Status:** ACTIVATED 2026-09-24 (Phase 5) — DEACTIVATED 2026-09-24 (post-Phase-5 checkpoint)  
**Ownership:** backend/app/services/ai/

---

### PHASE 7 AGENTS

#### SECURITY ENGINEER
**Status:** ACTIVATED 2026-09-25 (Phase 7)  
**Planned Activation:** Phase 7  
**Responsibilities:** Security review, audit, vulnerability assessment

#### RELEASE / DOCUMENTATION ENGINEER
**Status:** Not yet activated — standby for Phase 7 deployment/documentation tasks  
**Planned Activation:** Phase 7  
**Responsibilities:** Release notes, deployment documentation

---

## Agent Activation Criteria

Before activating any specialist agent, the MASTER must evaluate:

1. **Why is this agent needed now?**
2. **What task requires it?**
3. **What context does it need?**
4. **What does it own?**
5. **What agents does it depend on?**
6. **What interfaces must already exist?**
7. **How will its work be verified?**

## File Ownership Rules

- Each specialist owns specific domains
- Multiple agents must NOT simultaneously redesign the same file
- When multiple domains need the same change:
  1. Discuss the interface first
  2. Implement the owner-side change
  3. Adapt the consumer
  4. QA validates both

## Parallel Execution Rules

**Default mode:** SERIAL / CONTROLLED execution

**Parallel execution allowed ONLY when:**
- Tasks are genuinely independent
- Ownership boundaries are explicit
- Shared interfaces are already defined
- No two agents are modifying the same files
- MASTER has verified integration risk is low

**Never allow:**
- Competing database schemas
- Competing API contracts
- Duplicate domain models
- Conflicting architectural implementations
- Simultaneous uncontrolled edits to shared files

---

## Activation History

| Agent | Activation Date | Phase | Reason |
|-------|----------------|-------|--------|
| MASTER / CTO | 2026-09-22 | Phase 0 | Project initialization |
| System Architect | 2026-09-22 | Phase 0 | Architectural documentation |
| Documentation / Context Engineer | 2026-09-22 | Phase 0 | Project context documentation |
| Database Engineer | 2026-09-22 | Phase 1 | Case foundation database schema |
| Backend Engineer | 2026-09-22 | Phase 1 | Case foundation API implementation |
| Blockchain Engineer | 2026-09-23 | Phase 2 | Provider abstraction, EthereumAdapter, canonical model |
| Graph / Intelligence Engineer | 2026-09-23 | Phase 2 | Bounded tracing, canonical graph, trace API |
| Database Engineer (Phase-2 extension) | 2026-09-23 | Phase 2 | Migration 002: trace_runs, transactions, graphs |
| Frontend Engineer | 2026-09-23 | Phase 3 | Investigation UI, React Flow canvas, case management |
| QA / Test Engineer | 2026-09-23 | Phase 3 | Component unit tests, regression suites, verification |
| VASP / Entity Intelligence Engineer | 2026-09-23 | Phase 4 Stage 3 | Entity Intelligence, VASP Attribution |
| Risk Engineer | 2026-09-24 | Phase 4 Stage 4 | Explainable Risk Engine |
| AI / Copilot Engineer | 2026-09-24 | Phase 5 | AI Copilot: grounding, tools, citations, safety, API, tests |
| Security Engineer | 2026-09-25 | Phase 7 | Security audit, OWASP mapping, findings register |
| QA / Test Engineer | 2026-09-25 | Phase 7 | TASK-P7-003 full regression, edge/error scenarios, verification gaps |

---

## Notes

- This registry is the single source of truth for agent team status
- All agent activations must be recorded here
- Agent definitions live in `.opencode/agents/`
- Phase 1 is CLOSED (2026-09-23)
- Phase 2 is CLOSED (2026-09-23) — all Phase-2 agents deactivated after checkpoint
- Phase 3 is CLOSED (2026-09-23) — all Phase-3 agents deactivated after checkpoint
- Phase 4 is CLOSED (2026-09-24) — all Phase-4 agents deactivated after checkpoint
- Phase 5 is CLOSED (2026-09-24) — AI / Copilot Engineer deactivated after checkpoint
- Phase 6 is CLOSED (2026-09-25) — MASTER / CTO only; no specialist agent was activated
- Documented limitation: real LLM/provider behavior UNVERIFIED (no `OPENAI_API_KEY` configured)
- Documented limitation: PDF export fails explicitly with `PDF_RENDERER_UNAVAILABLE` when no renderer library is installed (never reported as a successful export)
- Migrations 004/005 prepared but not applied (DB connectivity unavailable)
- Phase 7 is AUTHORIZED (2026-09-25) and IN PROGRESS — Security Engineer activated (TASK-P7-001/002); QA / Test Engineer activated (TASK-P7-003); Release / Documentation Engineer still on standby
- Do NOT activate Release / Documentation or other agents until their Phase 7 tasks begin
- TASK-P7-003 report: `docs/PHASE_7_REGRESSION_REPORT.md` — backend 310/310, frontend 14/14, lint/build clean; coverage NOT MEASURED (GAP-COV-1); checkpoint commit NOT created pending MASTER review
