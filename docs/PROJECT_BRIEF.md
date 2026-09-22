# LedgerLens Project Brief

**Last Updated:** 2026-09-22T09:43:57Z  
**Project Phase:** PHASE 0 — FOUNDATION

---

## Mission Statement

Build a production-oriented MVP blockchain intelligence workstation that helps investigators trace cryptocurrency fraud by analyzing victim-reported suspect wallet addresses, identifying fund flows, detecting intermediary wallets, attributing destinations to known VASPs/exchanges, and generating explainable investigation reports.

---

## Problem Statement

**Title:**  
Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges from Victim-Reported Suspect Wallet Addresses through Automated Blockchain Analytics

**Context:**

Cyber-fraud victims report cryptocurrency wallet addresses used by fraudsters in various criminal activities:
- Investment scams
- Task-based fraud
- Sextortion
- Ransomware
- Phishing
- Darknet transactions
- Organized cyber-enabled financial crime

These reported addresses may be:
- Non-custodial wallets
- Burner wallets
- Intermediary wallets
- Layering/laundering wallets

**Investigator Challenge:**

When an investigator receives a victim-reported wallet address, they need to quickly understand:

1. Where did the funds move?
2. Which intermediary wallets were involved?
3. How many hops were involved?
4. Did the funds move across chains?
5. Is the destination associated with a known service/entity/VASP?
6. Why is this wallet or flow suspicious?
7. What evidence should be preserved for further investigation?

**Current Gap:**

Manual blockchain analysis is time-consuming and requires specialized expertise. Commercial tools are expensive and may not be accessible to all investigative agencies. A focused, explainable, investigator-centric tool is needed.

---

## Solution: LedgerLens

LedgerLens provides automated blockchain analytics to answer the core investigator question:

**"Given a victim-reported wallet, what happened to the funds, where did they travel, what intermediaries were involved, and what identifiable service/entity/VASP did the trail reach?"**

### Core Workflow

```
VICTIM / INVESTIGATOR CASE
        ↓
SUSPECT WALLET / TX HASH
        ↓
BLOCKCHAIN + ASSET IDENTIFICATION
        ↓
TRANSACTION INGESTION
        ↓
NORMALIZED TRANSACTION MODEL
        ↓
FUND-FLOW GRAPH
        ↓
MULTI-HOP TRACE
        ↓
INTERMEDIARY / BURNER PATTERN DETECTION
        ↓
ENTITY / ADDRESS INTELLIGENCE
        ↓
VASP / SERVICE ATTRIBUTION
        ↓
EXPLAINABLE RISK ANALYSIS
        ↓
INVESTIGATOR INTERPRETATION
        ↓
EVIDENCE PRESERVATION
        ↓
INVESTIGATION REPORT
```

---

## MVP Scope

### In Scope

**CORE:**
- Case intake (wallet address, transaction hash, fraud type, reported amount)
- Ethereum support (Phase 2)
- TRON support if feasible within MVP architecture (Phase 2+)
- Normalized blockchain transaction model
- Configurable hop tracing (depth, branch limits, dust filtering)
- Transaction graph generation
- Intermediary wallet analysis
- Suspicious flow pattern detection
- Address/entity registry
- VASP/service attribution
- Explainable risk scoring
- Investigator dashboard
- Evidence panel (pinning transactions/wallets, notes)
- Report generation
- AI investigation assistant (Phase 5)

**ARCHITECTURE PREPARATION:**
- Solana, Bitcoin, additional chains
- Bridges, mixers, DeFi protocols
- Cross-chain tracing
- Authorized external intelligence sources
- Future LEA integrations

### Out of Scope (MVP)

- Live mempool monitoring
- Real-time unconfirmed transaction streaming
- Full commercial Chainalysis feature parity
- Official integration with NCRP/Sahyog/exchanges without authorization
- Autonomous legal judgments
- Guaranteed VASP attribution without uncertainty representation

### Clear Labeling Required

The system must clearly distinguish:
- Prototype intelligence
- Curated data
- Heuristic inference
- Externally verified information
- Unknown/unattributed entities

---

## Key Principles

### 1. Explainability Over Black-Box
Every classification must be explainable:
- Risk scores must show contributing factors
- VASP attribution must show evidence and confidence
- Pattern detection must reference specific transactions

❌ "Risk = 93 because AI says so."  
✅ "Risk = 87/100: +25 known malicious association, +20 rapid onward transfer, +15 high fan-in, +12 layering pattern, +10 service interaction, +05 repeated case linkage"

### 2. Human-in-the-Loop
The system provides intelligence, NOT legal conclusions.

Use language such as:
- "associated with"
- "likely associated with"
- "probable match"
- "candidate entity"
- "confidence: 0.82"
- "requires investigator verification"

### 3. Provider-Agnostic Architecture
Do NOT couple directly to a single blockchain API provider.

Use adapter pattern:
```
BlockchainAdapter → Chain-specific Adapter → Provider Abstraction → External Provider
```

Ethereum: Alchemy (primary), Etherscan (secondary/enrichment)  
TRON: TronGrid  
Future: Solana, Bitcoin adapters

### 4. Separation of Concerns
Distinguish:
- **ON-CHAIN FACTS** (blockchain-verified transactions)
- **ENTITY INTELLIGENCE** (attribution, clustering, heuristics)

Never represent intelligence as if it were directly observed blockchain fact.

### 5. Security First
- Secrets never committed
- API keys server-side only
- Environment variables protected
- Input validation
- Report sanitization
- Demo data clearly marked

### 6. Single Source of Truth
One canonical implementation per concept:
- Transaction normalization → one service
- Risk calculation → one engine
- Entity attribution → one engine
- Graph generation → one model

### 7. Failure Transparency
Never hide:
- Provider failures
- Rate limits
- Missing data
- Uncertain attribution

Expose meaningful system state:
- KNOWN
- LIKELY
- POSSIBLE
- UNKNOWN
- FAILED_TO_RETRIEVE

---

## System Modules

### MODULE 1 — Case Intake
Wallet/transaction input, validation, case creation

### MODULE 2 — Blockchain Adapters
Chain-agnostic adapter interface, Ethereum/TRON implementations

### MODULE 3 — Transaction Normalizer
Convert chain-specific formats to canonical model

### MODULE 4 — Graph Engine
Wallet/transaction graph, hop tracing, branch control

### MODULE 5 — Pattern Engine
Detect peel chains, layering, rapid forwarding, high fan-in/out, consolidation

### MODULE 6 — Entity/Address Intelligence
Registry of known entities, VASPs, mixers, bridges, scam addresses

### MODULE 7 — VASP Attribution
Flagship module: match destinations to known exchanges/VASPs with confidence

### MODULE 8 — Risk Engine
Deterministic, explainable, versioned risk scoring

### MODULE 9 — Investigator Copilot
LLM-based assistant grounded in case data (Phase 5)

### MODULE 10 — Evidence
Pin transactions/wallets, save notes, preserve timestamps

### MODULE 11 — Reporting
Generate structured investigation reports with evidence

---

## Success Criteria

The MVP is successful when an investigator can:

1. Input a victim-reported wallet address
2. Automatically trace fund flows across multiple hops
3. Visualize the transaction graph
4. Identify intermediary wallets and patterns
5. See candidate VASP/exchange attribution with confidence scores
6. Understand WHY the system flagged specific wallets/transactions
7. Pin evidence and add investigator notes
8. Generate a comprehensive investigation report

The system should feel like an **actual investigator's blockchain intelligence workstation**, not an AI-generated dashboard.

---

## Reference Prototype

An earlier prototype exists at: https://trace-chain-spark.lovable.app

**Use ONLY as:**
- Product inspiration
- UX reference
- Feature reference
- Terminology reference

**Do NOT:**
- Copy architecture blindly
- Assume backend is production quality
- Preserve implementation for compatibility

The new MVP is engineered cleanly from first principles.

---

## Non-Goals

- Replace commercial blockchain intelligence platforms
- Provide legal conclusions
- Guarantee attribution accuracy
- Support all blockchains simultaneously in MVP
- Live mempool monitoring
- Regulatory integration without authorization

---

## Development Approach

- **Phase 0:** Foundation, architecture, documentation (CURRENT)
- **Phase 1:** Case foundation, database, basic backend
- **Phase 2:** Blockchain adapters, transaction tracing
- **Phase 3:** Investigation UI
- **Phase 4:** Intelligence (patterns, VASP attribution, risk)
- **Phase 5:** AI copilot
- **Phase 6:** Reporting
- **Phase 7:** Hardening

Progressive agent activation. Serial execution by default. Architecture over hacks.

---

## Alignment with SIH

This project addresses the Smart India Hackathon problem statement by:

1. Providing real-time automated blockchain analytics
2. Identifying fraud-linked cryptocurrency exchanges/VASPs
3. Accepting victim-reported suspect wallet addresses as input
4. Tracing fund flows and intermediary wallets
5. Generating explainable investigation intelligence
6. Supporting investigative workflows with evidence preservation

**Built for investigators. Grounded in evidence. Explainable by design.**
