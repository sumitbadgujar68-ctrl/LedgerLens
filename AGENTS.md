# LedgerLens Agent Registry

**Last Updated:** 2026-09-23  
**Current Phase:** PHASE 2 — BLOCKCHAIN FOUNDATION (CLOSED ✅)  
**Previous Phase:** PHASE 1 — CASE FOUNDATION (CLOSED ✅)

## Purpose

This file tracks the OpenCode agent team structure, activation status, and ownership boundaries for the LedgerLens project.

## Progressive Agent Activation Policy

The LedgerLens team follows a **progressive agent activation** strategy:

- Agents are activated **only when needed** for current phase work
- Agents are **NOT created merely because their role exists** in the long-term team specification
- The MASTER evaluates necessity before every agent activation
- Parallel agent execution requires explicit ownership boundaries, stable interfaces, and MASTER approval
- Serial/controlled execution is the default mode

## Current Active Agents (Phase 2)

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

### SYSTEM ARCHITECT (ACTIVE)
**Status:** Active  
**Activated:** 2026-09-22  
**Responsibilities:**
- Architecture design
- Module boundaries
- Service contracts
- Technology decisions
- Architectural Decision Records (ADRs)
- Cross-module consistency

**Ownership:**
- docs/ARCHITECTURE.md
- docs/DOMAIN_MODEL.md
- docs/API_CONTRACT.md (initial)
- docs/DATA_MODEL.md (initial)
- docs/DECISIONS.md

---

### DOCUMENTATION / CONTEXT ENGINEER (ACTIVE)
**Status:** Active  
**Activated:** 2026-09-22  
**Responsibilities:**
- Project memory maintenance
- Context file creation
- Developer onboarding materials
- Documentation standards

**Ownership:**
- README.md
- docs/PROJECT_BRIEF.md
- docs/SECURITY_MODEL.md
- docs/TEAM_PROTOCOL.md
- docs/ROADMAP.md
- docs/STATUS.md
- tasks/TASK_BOARD.md

---

## Planned Future Agents (Not Yet Active)

The following agents represent the complete long-term team structure.  
**They will be activated progressively according to actual development needs.**

### DATABASE ENGINEER (ACTIVE)
**Status:** Active  
**Activated:** 2026-09-22  
**Responsibilities:**
- Database schema design
- Migration file creation
- Data model implementation
- Database constraints and indexes
- Database testing

**Ownership:**
- database/
- migrations/
- docs/DATA_MODEL.md (implementation updates)

---

### BACKEND ENGINEER (ACTIVE)
**Status:** Active  
**Activated:** 2026-09-22  
**Responsibilities:**
- FastAPI application implementation
- API endpoint implementation
- Business logic services
- Request/response validation
- API testing

**Ownership:**
- backend/
- API implementation against database schema
- docs/API_CONTRACT.md (implementation updates)

---

### PHASE 2 AGENTS (ACTIVE)

#### BLOCKCHAIN ENGINEER (ACTIVE)
**Status:** Active  
**Activated:** 2026-09-23  
**Responsibilities:**
- Blockchain adapter interface definition
- EthereumAdapter implementation
- Provider abstraction (EthereumProvider)
- Alchemy provider implementation (verified against official API docs)
- Canonical transaction model
- Provider response normalization (Decimal-safe amounts)
- Pagination, rate-limit, and provider failure handling
- Provider/normalization unit tests

**Ownership:**
- backend/app/services/blockchain/
- Canonical transaction contract (consumed by Graph Engineer)

---

#### GRAPH / INTELLIGENCE ENGINEER (ACTIVE)
**Status:** Active  
**Activated:** 2026-09-23  
**Responsibilities:**
- Canonical graph model (nodes/edges, frontend-independent)
- Deterministic bounded multi-hop tracing (BFS)
- Hop/branch/dust/amount filters, cycle + dedup handling
- Case ↔ trace integration (references Phase-1 Case model)
- Trace API (POST/GET cases/{id}/traces)
- Trace/graph unit tests

**Ownership:**
- backend/app/services/graph/
- backend/app/services/tracing/
- backend/app/api/v1/traces.py (Phase-2 endpoints, contract approved by MASTER)

**Depends on:** Blockchain Engineer canonical interfaces (approved by MASTER before implementation)

---

### PHASE 3 AGENTS

#### FRONTEND ENGINEER
**Planned Activation:** Phase 3  
**Ownership:** frontend/

#### QA / TEST ENGINEER
**Planned Activation:** Phase 3  
**Ownership:** tests/

---

### PHASE 4 AGENTS

#### VASP / ENTITY INTELLIGENCE ENGINEER
**Planned Activation:** Phase 4  
**Ownership:** services/entity/, services/attribution/

#### RISK ENGINEER
**Planned Activation:** Phase 4  
**Ownership:** services/risk/

---

### PHASE 5 AGENTS

#### AI / COPILOT ENGINEER
**Planned Activation:** Phase 5  
**Ownership:** services/ai/

---

### PHASE 6-7 AGENTS

#### SECURITY ENGINEER
**Planned Activation:** Phase 6-7  
**Responsibilities:** Security review, audit, vulnerability assessment

#### RELEASE / DOCUMENTATION ENGINEER
**Planned Activation:** Phase 6-7  
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

---

## Notes

- This registry is the single source of truth for agent team status
- All agent activations must be recorded here
- Agent definitions live in `.opencode/agents/`
- Phase 1 is CLOSED (2026-09-23)
- Phase 2 is CLOSED (2026-09-23) — all Phase-2 agents deactivated after checkpoint
- Phase 3 is NOT started and NOT authorized
- Do NOT activate Frontend / QA / VASP / Risk / AI / Security / Release agents until Phase 3 authorization
