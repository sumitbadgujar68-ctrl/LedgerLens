# LedgerLens System Architecture

**Last Updated:** 2026-09-22  
**Phase:** PHASE 0 — FOUNDATION  
**Status:** Initial Architecture

---

## 1. System Overview

LedgerLens is a blockchain intelligence workstation designed to assist investigators in tracing cryptocurrency fraud through victim-reported wallet addresses. The system provides automated blockchain analytics, fund-flow visualization, VASP attribution, and explainable risk scoring.

**Core Objective:**  
Answer the investigator question: *"Given a victim-reported wallet, what happened to the funds, where did they travel, what intermediaries were involved, and what identifiable service/entity/VASP did the trail reach?"*

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                          │
│  React/Next.js, TypeScript, Tailwind CSS                        │
│  - Investigation Dashboard                                      │
│  - Case Intake                                                  │
│  - Transaction Graph Visualization                              │
│  - Evidence Panel                                               │
│  - Report Generation UI                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API (JSON)
┌────────────────────────────┴────────────────────────────────────┐
│                         BACKEND LAYER                           │
│  Python, FastAPI, Pydantic                                      │
│  - API Routes & Controllers                                     │
│  - Business Services Orchestration                              │
│  - Authentication & Authorization                               │
│  - Background Job Coordination                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐  ┌─────────▼────────┐  ┌───────▼───────┐
│  DOMAIN       │  │  INTELLIGENCE    │  │  BLOCKCHAIN   │
│  SERVICES     │  │  SERVICES        │  │  SERVICES     │
├───────────────┤  ├──────────────────┤  ├───────────────┤
│ Case          │  │ Pattern Engine   │  │ Adapter       │
│ Management    │  │ VASP Attribution │  │ Abstraction   │
│               │  │ Risk Engine      │  │               │
│ Evidence      │  │ Entity Registry  │  │ Transaction   │
│ Management    │  │                  │  │ Normalizer    │
│               │  │ Graph Engine     │  │               │
│ Report        │  │                  │  │ Provider      │
│ Generation    │  │ AI Copilot       │  │ Abstraction   │
│               │  │ (Phase 5)        │  │               │
└───────┬───────┘  └─────────┬────────┘  └───────┬───────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                       DATA LAYER                                │
│  PostgreSQL / Supabase                                          │
│  - Cases                                                        │
│  - Wallets & Transactions                                       │
│  - Entities & Addresses                                         │
│  - Evidence & Notes                                             │
│  - Risk Scores & Patterns                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   EXTERNAL BLOCKCHAIN PROVIDERS                 │
│  Alchemy (Ethereum), Etherscan (Ethereum), TronGrid (TRON)      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Architectural Principles

### 3.1 Provider-Agnostic Design

**Principle:**  
LedgerLens must NOT be coupled to a single blockchain API provider.

**Architecture:**
```
Application Domain Logic
        ↓
BlockchainAdapter (Interface)
        ↓
Chain-Specific Adapter (EthereumAdapter, TronAdapter, etc.)
        ↓
Provider Abstraction (AlchemyProvider, EtherscanProvider, TronGridProvider)
        ↓
External Blockchain Provider API
```

**Benefits:**
- Swap providers without rewriting domain logic
- Combine multiple providers for enrichment/fallback
- Add new chains by implementing adapter interface
- Provider-specific formats isolated from core system

**Constraint:**  
Provider details (response formats, pagination schemes, error codes) must NEVER leak into graph engine, risk engine, attribution engine, frontend, or AI copilot.

---

### 3.2 Canonical Transaction Model

**Principle:**  
All blockchain data must be normalized into a single canonical transaction representation before consumption by downstream services.

**Flow:**
```
Provider Raw Response → Chain Adapter → Canonical Transaction → Domain Services
```

**Canonical Model Fields:**
- chain (string)
- transaction_hash (string)
- block_number (integer)
- timestamp (datetime)
- from_address (string)
- to_address (string)
- asset_symbol (string)
- amount (decimal)
- token_contract_address (string, nullable)
- transaction_type (enum: transfer, contract_call, token_transfer, etc.)
- gas_fee (decimal)
- status (enum: confirmed, failed, pending)
- provider_source (string)
- raw_provider_data_ref (json, optional for debugging)

**Rationale:**
- Single source of truth for transaction representation
- Ethereum USDT transfer and TRON TRC-20 transfer have identical canonical structure
- Downstream services (graph, risk, VASP attribution) consume only canonical model
- Simplifies multi-chain support

---

### 3.3 Separation of Concerns: Facts vs. Intelligence

**Principle:**  
Distinguish on-chain facts from entity intelligence.

**On-Chain Facts:**
- Address A sent 1,200 USDT to Address B at block 18234567
- Directly observable, verifiable blockchain data
- Source: blockchain providers

**Entity Intelligence:**
- Address B is a candidate match for Binance Hot Wallet 14 (confidence: 0.82)
- Inference based on clustering, patterns, historical data
- Source: entity intelligence engine

**Architectural Enforcement:**
- Transaction records store on-chain facts
- Entity attribution records store intelligence with confidence/evidence
- Frontend displays both with clear provenance labels
- Reports distinguish verified facts from inferred intelligence

**Forbidden:**
Never represent "likely Binance" as if it were a directly observed blockchain property.

---

### 3.4 Explainability Over Black-Box

**Principle:**  
Every classification must be explainable and traceable to underlying evidence.

**Risk Scoring Example:**
```
Risk Score: 87/100

Contributing Factors:
+25  Known malicious association (Entity: ScamDB Record #4521)
+20  Rapid onward transfer (<2 hours)
+15  High fan-in (received from 47 unique addresses in 24h)
+12  Layering pattern detected (3-hop peel chain)
+10  Interaction with mixer service (Tornado Cash)
+05  Repeated case linkage (3 prior cases)

Evidence:
- Transaction: 0xabc123... (2026-09-20 14:23:11 UTC)
- Transaction: 0xdef456... (2026-09-20 16:05:03 UTC)
- Entity Match: Tornado Cash Router (0x123abc...)
```

**Implementation:**
- Risk engine returns structured breakdown
- Each factor references specific transactions/entities/patterns
- Score calculation is versioned and deterministic
- Frontend displays factor list with evidence links

---

### 3.5 Single Source of Truth

**Principle:**  
One canonical implementation per domain concept.

**Examples:**
- Transaction normalization → `TransactionNormalizer` service
- Risk calculation → `RiskEngine` service
- Entity attribution → `AttributionEngine` service
- Graph generation → `GraphEngine` service
- VASP matching → `VASPMatcher` service

**Anti-Pattern:**
Do NOT allow:
- Frontend calculating risk scores independently
- Multiple risk calculation implementations
- Duplicate entity matching logic in different modules

**Enforcement:**
- Services expose well-defined interfaces
- Domain logic resides in service layer only
- API controllers orchestrate, not implement domain logic

---

### 3.6 Human-in-the-Loop

**Principle:**  
The system provides intelligence and recommendations, NOT definitive legal conclusions.

**Language:**
- ✅ "associated with", "likely associated with", "candidate entity"
- ✅ "confidence: 0.82", "requires investigator verification"
- ✅ "evidence indicates", "probable match"
- ❌ "definitely owned by", "confirmed criminal wallet"
- ❌ "legally proven", "conclusively identified"

**Implementation:**
- All attribution includes confidence scores
- All risk scores show contributing factors
- Reports include "Limitations" section
- UI emphasizes investigator interpretation role

---

### 3.7 Failure Transparency

**Principle:**  
Never hide provider failures, rate limits, or missing data.

**Error States:**
- `PROVIDER_TIMEOUT`
- `PROVIDER_RATE_LIMIT`
- `PROVIDER_UNAVAILABLE`
- `DATA_INCOMPLETE`
- `ADDRESS_INVALID`
- `CHAIN_UNSUPPORTED`

**Implementation:**
- API responses include provider status
- Frontend displays data availability state
- Reports note incomplete data
- Distinguish "no activity" from "unable to retrieve data"

**Anti-Pattern:**
Never silently treat missing blockchain data as zero activity.

---

## 4. Module Boundaries

### 4.1 Case Management Module

**Responsibilities:**
- Case intake and validation
- Wallet/transaction hash input
- Case metadata management
- Case lifecycle tracking
- Investigator assignment

**Interfaces:**
- `POST /cases` — Create case
- `GET /cases/{case_id}` — Retrieve case
- `PUT /cases/{case_id}` — Update case
- `GET /cases/{case_id}/timeline` — Get case activity timeline

**Owned Entities:**
- Case
- Wallet (linked to case)
- CaseMetadata

---

### 4.2 Blockchain Adapter Module

**Responsibilities:**
- Define `BlockchainAdapter` interface
- Implement chain-specific adapters (Ethereum, TRON, etc.)
- Abstract provider interactions
- Handle provider failures and retries
- Normalize responses to canonical model

**Interfaces:**
- `validate_address(chain, address) → bool`
- `fetch_transaction_history(chain, address, filters) → List[CanonicalTransaction]`
- `fetch_transaction_details(chain, tx_hash) → CanonicalTransaction`
- `fetch_token_transfers(chain, address, filters) → List[CanonicalTransaction]`

**Owned Entities:**
- CanonicalTransaction
- BlockchainAdapter (interface)
- EthereumAdapter
- TronAdapter (Phase 2+)

---

### 4.3 Transaction Normalizer Module

**Responsibilities:**
- Convert provider-specific formats to canonical model
- Handle chain-specific transaction types
- Extract token transfers from contract calls
- Preserve raw provider data reference

**Interfaces:**
- `normalize_ethereum_transaction(provider_response) → CanonicalTransaction`
- `normalize_tron_transaction(provider_response) → CanonicalTransaction`

---

### 4.4 Graph Engine Module

**Responsibilities:**
- Build wallet/transaction graph
- Multi-hop breadth-first traversal
- Branch limiting and dust filtering
- Amount threshold enforcement
- Direction control (inbound/outbound)
- Time window filtering

**Interfaces:**
- `build_graph(wallet, depth, filters) → Graph`
- `expand_graph(graph, additional_hops) → Graph`
- `get_intermediaries(graph, source, destination) → List[Wallet]`

**Owned Entities:**
- Graph (nodes: wallets, edges: transactions)
- TraceConfig (depth, branch_limit, dust_threshold, etc.)

---

### 4.5 Pattern Engine Module

**Responsibilities:**
- Detect suspicious transaction patterns
- Identify peel chains, layering, rapid forwarding
- Calculate fan-in/fan-out metrics
- Detect consolidation/split patterns
- Identify mixer/bridge interactions

**Interfaces:**
- `detect_patterns(graph) → List[Pattern]`
- `classify_wallet_behavior(wallet, transactions) → WalletBehavior`

**Owned Entities:**
- Pattern (type, confidence, evidence)
- WalletBehavior (classification, metrics)

**Detected Patterns:**
- Peel chain
- Rapid forwarding (<N hours)
- High fan-in (>N sources in timeframe)
- High fan-out (>N destinations in timeframe)
- Layering
- Consolidation
- Split-and-forward
- Mixer interaction
- Bridge interaction

---

### 4.6 Entity / Address Intelligence Module

**Responsibilities:**
- Maintain entity registry
- Known VASPs, exchanges, mixers, bridges
- Scam-linked addresses
- Case-linked wallets
- Entity clustering

**Interfaces:**
- `lookup_entity(chain, address) → Optional[Entity]`
- `register_entity(entity_data) → Entity`
- `get_candidates(chain, address) → List[EntityCandidate]`

**Owned Entities:**
- Entity (name, type, addresses, source, confidence)
- EntityType (exchange, vasp, mixer, bridge, protocol, scam, unknown)
- EntityCandidate (candidate matches with confidence)

---

### 4.7 VASP Attribution Module

**Responsibilities:**
- Match destination addresses to VASPs/exchanges
- Calculate attribution confidence
- Provide evidence chain
- Support multiple matching strategies

**Interfaces:**
- `attribute_vasp(chain, address) → VASPAttribution`
- `get_attribution_evidence(attribution_id) → List[Evidence]`

**Matching Strategies:**
- Exact address match (known deposit/hot wallet)
- Cluster match (address belongs to known cluster)
- Behavioral similarity
- Historical transaction relationships
- Multiple independent signals

**Owned Entities:**
- VASPAttribution (candidate_entity, confidence, evidence, source)

---

### 4.8 Risk Engine Module

**Responsibilities:**
- Calculate explainable risk scores
- Define risk factors and weights
- Version scoring logic
- Generate risk explanations

**Interfaces:**
- `calculate_risk(wallet, transactions, context) → RiskScore`
- `explain_risk(risk_score_id) → RiskExplanation`

**Risk Factors:**
- Known malicious association
- Rapid onward transfer
- High fan-in
- High fan-out
- Layering pattern
- Short holding period
- Mixer interaction
- Repeated case linkage
- VASP interaction patterns

**Owned Entities:**
- RiskScore (score, category, factors, version)
- RiskFactor (type, weight, evidence)
- RiskCategory (low, medium, high, critical)

---

### 4.9 Evidence Module

**Responsibilities:**
- Pin transactions and wallets
- Investigator notes
- Evidence timestamping
- Evidence association with cases

**Interfaces:**
- `pin_transaction(case_id, tx_hash, note) → Evidence`
- `pin_wallet(case_id, address, note) → Evidence`
- `add_note(case_id, content) → Note`
- `get_case_evidence(case_id) → List[Evidence]`

**Owned Entities:**
- Evidence (type, reference, note, timestamp, investigator)
- Note (content, timestamp, investigator)

---

### 4.10 Reporting Module

**Responsibilities:**
- Generate investigation reports
- Aggregate case data
- Format evidence for export
- PDF/JSON/HTML export

**Interfaces:**
- `generate_report(case_id, format) → Report`
- `export_report(report_id, format) → File`

**Report Sections:**
- Case information
- Initial reported wallet
- Methodology
- Transaction timeline
- Graph summary
- Intermediary wallets
- Destination entities
- VASP attribution
- Risk analysis
- Evidence references
- Investigator notes
- Limitations
- Generated timestamp

---

### 4.11 AI Copilot Module (Phase 5)

**Responsibilities:**
- LLM-based investigation assistant
- Grounded in case data
- Answer investigator questions
- Generate summaries
- Explain risk scores

**Interfaces:**
- `ask_copilot(case_id, question) → Answer`
- `summarize_case(case_id) → Summary`
- `explain_score(risk_score_id) → Explanation`

**Constraints:**
- MUST cite underlying data
- MUST NOT invent evidence
- MUST NOT fabricate transaction hashes, entities, or attribution
- Operates only on available case data

---

## 5. Data Flow

### 5.1 Case Creation Flow

```
Investigator Input (wallet/tx_hash)
        ↓
Case Management Module (validation, create case)
        ↓
Database (persist case)
        ↓
Background Job (initiate trace)
        ↓
Blockchain Adapter (fetch transactions)
        ↓
Transaction Normalizer (canonical model)
        ↓
Database (persist transactions)
        ↓
Graph Engine (build graph)
        ↓
Pattern Engine (detect patterns)
        ↓
Entity Intelligence (lookup entities)
        ↓
VASP Attribution (match destinations)
        ↓
Risk Engine (calculate scores)
        ↓
Database (persist analysis results)
        ↓
Frontend (display investigation dashboard)
```

---

### 5.2 Transaction Ingestion Flow

```
Chain Adapter Request → Provider API → Provider Response
        ↓
Provider Abstraction Layer (error handling, retry)
        ↓
Transaction Normalizer (canonical model)
        ↓
Validation (schema validation, business rules)
        ↓
Database Persistence
        ↓
Event Emission (for downstream processing)
```

---

### 5.3 VASP Attribution Flow

```
Destination Address (from graph)
        ↓
Entity Intelligence (lookup known entities)
        ↓
VASP Matcher (exact match, cluster match, behavioral match)
        ↓
Confidence Calculation (multiple signals)
        ↓
Evidence Aggregation
        ↓
Attribution Record (candidate, confidence, evidence)
        ↓
Database Persistence
        ↓
Frontend Display (with confidence and evidence)
```

---

## 6. Technology Stack Rationale

### 6.1 Frontend: React/Next.js + TypeScript

**Rationale:**
- Modern component-driven UI
- TypeScript for type safety
- Next.js for SSR/API routes if needed
- Rich ecosystem for graph visualization (react-force-graph, D3.js)
- Tailwind CSS for consistent styling

---

### 6.2 Backend: Python + FastAPI

**Rationale:**
- Python: Strong blockchain library ecosystem (web3.py, tronpy)
- FastAPI: Modern, async, auto-generated OpenAPI docs
- Pydantic: Strong schema validation
- Easier integration with ML/AI libraries (Phase 5)

---

### 6.3 Database: PostgreSQL + Supabase

**Rationale:**
- PostgreSQL: Robust relational database, JSON support, complex queries
- Supabase: Managed PostgreSQL, real-time subscriptions, auth, API generation
- Strong constraint enforcement
- Graph query support with recursive CTEs

---

### 6.4 Blockchain: Adapter-Based Architecture

**Rationale:**
- Alchemy: Reliable Ethereum provider, comprehensive API
- Etherscan: Enrichment/fallback for Ethereum
- TronGrid: TRON network support
- Adapter pattern allows provider swapping without domain logic changes

---

## 7. Deployment Architecture (Conceptual)

### 7.1 MVP Deployment

```
┌─────────────────────────┐
│   Frontend (Vercel)     │
│   React/Next.js         │
└───────────┬─────────────┘
            │ HTTPS
┌───────────▼─────────────┐
│   Backend (Railway)     │
│   FastAPI + Workers     │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│   Database (Supabase)   │
│   PostgreSQL            │
└─────────────────────────┘

External:
- Alchemy API
- Etherscan API
- TronGrid API
```

### 7.2 Environment Configuration

**Environments:**
- Development (local)
- Staging (pre-production testing)
- Production (investigator use)

**Secrets Management:**
- Environment variables via .env files (local)
- Platform secrets management (Railway, Vercel)
- Never commit secrets to repository

---

## 8. Development Standards

### 8.1 Code Organization

**Backend:**
```
backend/
├── api/                 # FastAPI routes
│   ├── v1/             # API version 1
│   │   ├── cases.py
│   │   ├── wallets.py
│   │   └── reports.py
├── services/           # Business logic
│   ├── blockchain/     # Blockchain adapters
│   ├── graph/          # Graph engine
│   ├── risk/           # Risk engine
│   ├── attribution/    # VASP attribution
│   └── evidence/       # Evidence management
├── models/             # Pydantic models
├── db/                 # Database models (SQLAlchemy)
├── workers/            # Background jobs
├── utils/              # Utilities
└── config.py           # Configuration
```

**Frontend:**
```
frontend/
├── components/         # React components
│   ├── common/        # Shared components
│   ├── case/          # Case-related components
│   ├── graph/         # Graph visualization
│   └── evidence/      # Evidence panel
├── pages/             # Next.js pages
├── services/          # API client
├── types/             # TypeScript types
├── hooks/             # Custom hooks
└── utils/             # Utilities
```

---

### 8.2 API Standards

**Conventions:**
- RESTful endpoints
- JSON request/response
- Consistent error format
- Pagination for list endpoints
- Versioned API routes (`/api/v1/...`)

**Error Response Format:**
```json
{
  "error": {
    "code": "PROVIDER_TIMEOUT",
    "message": "Blockchain provider request timed out",
    "details": {
      "provider": "alchemy",
      "chain": "ethereum"
    }
  }
}
```

---

### 8.3 Testing Strategy

**Unit Tests:**
- Pure business logic
- Adapters (mocked providers)
- Normalizers
- Risk calculations

**Integration Tests:**
- API endpoints (mocked external services)
- Database operations
- Service orchestration

**End-to-End Tests:**
- Complete investigation workflow
- Case creation → trace → report

**Test Data:**
- Fixtures for known patterns
- Demo investigation scenarios
- Clearly marked as synthetic

---

### 8.4 Logging & Observability

**Log Levels:**
- DEBUG: Development details
- INFO: Normal operations
- WARNING: Degraded state (provider slow, rate limit approaching)
- ERROR: Operation failures
- CRITICAL: System failures

**Logged Events:**
- Case creation
- Blockchain API requests
- Provider failures
- Risk score calculations
- VASP attribution matches
- Report generation

**Security:**
- Never log full API keys
- Never log wallet private keys (system never handles private keys)
- Sanitize sensitive data

---

### 8.5 Security Standards

**API Security:**
- Authentication required for all endpoints (except public health check)
- JWT tokens for session management
- Rate limiting per IP/user
- Input validation on all endpoints

**Data Security:**
- Secrets in environment variables only
- API keys server-side only
- Database credentials protected
- Report sanitization (no XSS in exported HTML)

**Blockchain Security:**
- Validate addresses before querying
- Never expose raw provider responses to frontend
- Rate limit blockchain queries

---

## 9. Cross-Cutting Concerns

### 9.1 Authentication & Authorization

**Phase 1 (MVP):**
- Simple investigator accounts
- Session-based authentication
- Role: Investigator (full access)

**Future:**
- Role-based access control (Admin, Investigator, Viewer)
- Audit logging
- Case assignment/ownership

---

### 9.2 Background Jobs

**Use Cases:**
- Multi-hop transaction trace (long-running)
- Graph expansion
- Entity enrichment
- Report generation

**Implementation:**
- Celery or FastAPI Background Tasks
- Job status tracking
- Progress updates
- Error recovery

---

### 9.3 Caching Strategy

**Cache Candidates:**
- Blockchain transaction data (immutable once confirmed)
- Entity registry lookups
- Known VASP addresses

**Cache Invalidation:**
- Time-based expiry
- Manual invalidation for entity updates

---

### 9.4 Error Handling

**Graceful Degradation:**
- If Alchemy fails, try Etherscan (Ethereum)
- If entity lookup fails, continue with "Unknown Entity"
- If risk calculation fails, display "Unable to calculate risk"

**User Feedback:**
- Clear error messages
- Distinguish user error from system error
- Actionable guidance where possible

---

## 10. Extensibility Points

### 10.1 Adding New Blockchains

**Steps:**
1. Implement `BlockchainAdapter` interface for new chain
2. Create provider abstraction for chain's data source
3. Implement transaction normalizer for chain's format
4. Add chain to supported chains enum
5. Update frontend chain selector

**No changes required:**
- Graph engine
- Risk engine
- VASP attribution
- Frontend graph visualization
- Report generation

---

### 10.2 Adding New Providers

**Steps:**
1. Implement provider abstraction interface
2. Add provider configuration
3. Update chain adapter to support new provider
4. Add provider fallback/enrichment logic

**No changes required:**
- Domain services
- Database schema
- Frontend

---

### 10.3 Adding New Risk Factors

**Steps:**
1. Define new risk factor in `RiskEngine`
2. Implement factor calculation logic
3. Assign factor weight
4. Update risk explanation template

**No changes required:**
- API contract
- Database schema (if using JSON for factors)
- Frontend (dynamic factor rendering)

---

## 11. Constraints & Trade-offs

### 11.1 MVP vs. Commercial Platform

**Constraint:**  
LedgerLens is an MVP, not a Chainalysis replacement.

**Trade-offs:**
- Limited blockchain support (Ethereum first, TRON Phase 2+)
- Heuristic entity attribution (not proprietary clustering algorithms)
- Manual entity registry curation (not automated global clustering)
- Asynchronous trace (not real-time mempool monitoring)

**Acceptance:**  
These are intentional MVP scope decisions, not architectural limitations.

---

### 11.2 Provider Dependency

**Constraint:**  
System depends on external blockchain providers.

**Mitigation:**
- Provider abstraction allows swapping
- Multiple provider support (primary + fallback)
- Graceful degradation on provider failure
- Clear error messaging

**Risk:**
- Provider rate limits
- Provider downtime
- Provider cost

---

### 11.3 VASP Attribution Uncertainty

**Constraint:**  
VASP attribution is probabilistic, not definitive.

**Mitigation:**
- Confidence scores required
- Evidence chain provided
- Multiple signals aggregated
- Clear "requires verification" messaging

**Acceptance:**  
This is an inherent limitation of blockchain intelligence, not an architectural flaw.

---

## 12. Architecture Verification Checklist

- [x] Provider-agnostic blockchain layer defined
- [x] Canonical transaction model specified
- [x] Module boundaries clearly defined
- [x] On-chain facts separated from intelligence
- [x] Explainability requirements enforced architecturally
- [x] Single source of truth per concept
- [x] Failure states explicitly handled
- [x] Human-in-the-loop design principle enforced
- [x] Extensibility points identified
- [x] Security principles integrated
- [x] MVP scope respected (no over-engineering)

---

## 13. Next Steps (Implementation Phases)

**Phase 1 (Case Foundation):**
- Implement Case Management Module
- Database schema for cases, wallets, transactions
- Basic FastAPI backend
- Database Engineer + Backend Engineer activated

**Phase 2 (Blockchain Foundation):**
- Implement Blockchain Adapter (Ethereum)
- Transaction Normalizer
- Graph Engine
- Blockchain Engineer + Graph Engineer activated

**Phase 3 (Investigation UI):**
- React frontend
- Investigation dashboard
- Graph visualization
- Frontend Engineer + QA Engineer activated

**Phase 4 (Intelligence):**
- Pattern Engine
- VASP Attribution
- Risk Engine
- VASP Engineer + Risk Engineer activated

**Phase 5 (AI Copilot):**
- LLM integration
- Grounded assistant
- AI Engineer activated

**Phase 6 (Reporting):**
- Report generation
- PDF export
- Release Engineer support

**Phase 7 (Hardening):**
- Security review
- Performance testing
- Security Engineer activated

---

**Document Status:** Initial architecture for Phase 0  
**Approval Required:** MASTER / CTO  
**Dependencies:** None (foundational document)
