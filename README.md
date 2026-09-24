# LedgerLens

**Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges from Victim-Reported Suspect Wallet Addresses through Automated Blockchain Analytics**

---

## Project Status

**Current Phase:** PHASE 6 — REPORTING (CLOSED ✅) — Next: Phase 7 (NOT STARTED)  
**Status:** Closed  
**Last Updated:** 2026-09-25

This is a production-oriented MVP for the Smart India Hackathon (SIH) problem statement focused on blockchain forensics and cryptocurrency fraud investigation.

---

## Overview

LedgerLens is a blockchain intelligence workstation designed to help investigators trace cryptocurrency fraud by:

1. Accepting victim-reported suspect wallet addresses
2. Automatically tracing fund flows across multiple hops
3. Identifying intermediary wallets and layering patterns
4. Attributing destination addresses to known VASPs/exchanges
5. Providing explainable risk scoring
6. Generating investigation reports with preserved evidence

**This is NOT:**
- A commercial Chainalysis replacement
- A real-time mempool monitoring system
- An autonomous legal judgment system

**This IS:**
- An investigator-centric blockchain forensics tool
- A system that provides explainable intelligence
- A human-in-the-loop investigation assistant

---

## Core Problem

Cyber-fraud victims report cryptocurrency wallet addresses used by fraudsters in:
- Investment scams
- Task-based fraud
- Sextortion
- Ransomware
- Phishing
- Darknet transactions
- Organized cyber-enabled financial crime

Investigators need to quickly understand:
- Where funds moved
- Which intermediary wallets were involved
- How many hops were involved
- Whether cross-chain movement occurred
- Which VASPs/exchanges the funds reached
- Why the wallet or flow is suspicious
- What evidence should be preserved

---

## Technology Stack

### Phase 0 (delivered)
- Project architecture and documentation
- Progressive agent team activation
- Repository structure and standards

### Planned Stack

**Frontend:**
- React / Next.js
- TypeScript
- Tailwind CSS
- Interactive transaction graph visualization

**Backend:**
- Python
- FastAPI
- Pydantic
- Async APIs

**Database:**
- PostgreSQL
- Supabase

**Blockchain:**
- Adapter-based architecture
- Ethereum (Phase 2)
- TRON (Phase 2+)
- Future: Solana, Bitcoin

**Intelligence:**
- Deterministic pattern detection
- Explainable risk scoring
- VASP/entity attribution engine

**AI:**
- LLM-based investigator copilot (Phase 5)
- Grounded in case data only
- Citation-based responses

---

## Development Phases

### ✅ PHASE 0 — FOUNDATION (Complete)
- Repository structure
- Project documentation
- Agent team establishment
- Coding standards
- Architecture definition

### ✅ PHASE 1 — CASE FOUNDATION (Complete)
- Case intake
- Wallet/transaction input
- Database schema
- Basic backend API

### ✅ PHASE 2 — BLOCKCHAIN FOUNDATION (Complete)
- Ethereum adapter
- Transaction normalization
- Multi-hop tracing
- Graph model

### ✅ PHASE 3 — INVESTIGATION UI (Complete)
- Dashboard
- Case management screen
- Transaction visualization
- Evidence panel

### ✅ PHASE 4 — INTELLIGENCE (Complete)
- Pattern detection
- VASP attribution
- Risk scoring
- Entity registry

### ✅ PHASE 5 — AI COPILOT (Complete — backend; real-provider verification UNVERIFIED)
- Investigator assistant
- Natural language Q&A
- Case summarization
- Risk explanation with citations
- Hallucination prevention (backend)

### ✅ PHASE 6 — REPORTING (Complete)
- Evidence capture and provenance
- Report generation (14 documented sections, no fabricated data)
- Export rendering: sanitized HTML, deterministic JSON, PDF
- Report API (generate / list / download) and artifact storage
- PDF export fails explicitly with `PDF_RENDERER_UNAVAILABLE` if no renderer is installed (never a fake successful export)

### PHASE 7 — HARDENING (NOT STARTED)
- Security audit
- Performance testing
- Deployment validation

---

## Project Documentation

Comprehensive project context is maintained in the `docs/` directory:

- **[MASTER_BOOTSTRAP.md](docs/MASTER_BOOTSTRAP.md)** — Governing project charter and operating specification
- **[PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md)** — Mission, problem statement, MVP scope
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** — System design, module structure
- **[STATUS.md](docs/STATUS.md)** — Current phase status and progress
- **[TEAM_PROTOCOL.md](docs/TEAM_PROTOCOL.md)** — Agent collaboration workflow
- **[DECISIONS.md](docs/DECISIONS.md)** — Architectural decision records (ADRs)

See **[AGENTS.md](AGENTS.md)** for the current agent team structure and activation status.

---

## Setup Instructions

**Phases 0–6 are complete. Phase 7 (Hardening) has NOT started.**  
Real LLM/provider behavior remains UNVERIFIED — no `OPENAI_API_KEY` is configured (documented limitation).  
See [docs/STATUS.md](docs/STATUS.md) for current status and [docs/ROADMAP.md](docs/ROADMAP.md) for the full plan.

---

## Reference Prototype

An earlier prototype exists at: https://trace-chain-spark.lovable.app

This prototype serves as:
- Product inspiration
- UX reference
- Feature reference
- Terminology reference

**The new LedgerLens MVP is being engineered cleanly from first principles.**  
The prototype's implementation is NOT being preserved for compatibility.

---

## Security & Compliance

- Blockchain API credentials remain server-side only
- No secrets committed to repository
- Demo data explicitly marked as synthetic
- System provides intelligence, NOT legal conclusions
- Human investigator verification required for all findings

---

## Contributing

This project follows a structured agent-based development process.

See:
- [AGENTS.md](AGENTS.md) — Agent team structure
- [docs/TEAM_PROTOCOL.md](docs/TEAM_PROTOCOL.md) — Collaboration workflow
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — System design

---

## License

_To be determined_

---

## Contact

_To be determined_

---

**Built for Smart India Hackathon (SIH)**  
**Quality > Quantity | Evidence > Assumptions | Architecture > Hacks**
