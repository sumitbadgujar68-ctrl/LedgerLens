# LedgerLens Known Limitations

**Last Updated:** 2026-09-22  
**Phase:** PHASE 0 — FOUNDATION  
**Status:** MVP Scope Boundaries and Constraints

---

## 1. Overview

This document explicitly defines what LedgerLens MVP is NOT, clarifies intentional scope limitations, documents known constraints, and identifies future enhancement candidates.

**Purpose:** Set realistic expectations and prevent scope creep.

---

## 2. MVP Scope Limitations

### 2.1 Not a Commercial Platform Replacement

**Limitation:**  
LedgerLens is an MVP demonstration, NOT a commercial Chainalysis/TRM Labs/Elliptic replacement.

**What this means:**
- Limited blockchain coverage (Ethereum primary, TRON optional)
- Heuristic entity attribution (not proprietary global clustering)
- Manual entity registry curation (not automated clustering)
- Demo/curated intelligence data (not real-time global intelligence feeds)
- No direct access to exchange APIs
- No law enforcement integrations without authorization

**Rationale:**  
MVP focuses on demonstrating core workflow and explainability, not competing with billion-dollar commercial platforms.

---

### 2.2 No Live Mempool Monitoring

**Limitation:**  
MVP does NOT monitor live mempool or stream unconfirmed transactions.

**What this means:**
- Tracing begins when investigator submits case
- Analysis uses confirmed blockchain data
- No real-time alerts for new transactions
- No live websocket streaming to frontend

**Rationale:**
- Live monitoring requires complex infrastructure
- Confirmed transactions are sufficient for fraud investigation (fraud already occurred)
- Out of MVP scope

**Future Enhancement:**
- Phase 8+: Live monitoring for ongoing cases
- Websocket updates for active investigations

---

### 2.3 Limited Blockchain Support

**Limitation:**  
MVP Phase 1-2 focuses on Ethereum only. TRON deferred to Phase 2+ if needed.

**What this means:**
- No Bitcoin support (MVP)
- No Solana support (MVP)
- No multi-chain simultaneous tracing (MVP)
- No cross-chain bridge tracing (MVP)
- Architecture supports future chains, but implementation deferred

**Rationale:**
- Ethereum has highest fraud volume
- Single-chain MVP reduces complexity
- Provider-agnostic architecture allows future expansion

**Future Enhancement:**
- Phase 8: TRON, Solana, Bitcoin adapters
- Phase 9: Cross-chain tracing

---

### 2.4 No Guaranteed VASP Attribution

**Limitation:**  
VASP attribution is probabilistic, NOT definitive.

**What this means:**
- Confidence scores always included
- "Likely Binance" not "Definitely Binance"
- Requires investigator verification
- False positives possible
- Uncertainty explicitly represented

**Rationale:**
- Blockchain addresses are pseudonymous
- Clustering is heuristic
- No direct exchange API access
- Human-in-the-loop by design

**Future Enhancement:**
- Phase 9: Advanced clustering
- Phase 11: Authorized exchange partnerships (if available)

---

### 2.5 No Autonomous Legal Conclusions

**Limitation:**  
System provides intelligence, NOT legal judgments.

**What this means:**
- Risk scores are advisory, not legal verdicts
- Attribution is candidate identification, not proof
- Pattern detection is evidence, not conclusion
- Always requires investigator interpretation
- Reports include disclaimers

**Rationale:**
- Legal conclusions require human judgment
- Blockchain analysis is one part of investigation
- Liability concerns
- Ethical responsibility

**This is NOT a limitation to fix. This is intentional design.**

---

### 2.6 No Official Integrations (Unless Authorized)

**Limitation:**  
MVP has NO official integrations with:
- NCRP (National Cyber Crime Reporting Portal)
- Sahyog platform
- Law enforcement systems
- Exchange APIs
- Commercial intelligence platforms

**What this means:**
- Data input is manual (investigator enters wallet)
- No automated case import from NCRP
- No automated evidence export to LEA systems
- Standalone tool initially

**Rationale:**
- Integration requires authorization
- Integration requires partnerships
- Out of MVP scope

**Future Enhancement:**
- Phase 11: Authorized LEA integrations (if approved)
- Phase 11: Exchange partnerships (if available)

---

## 3. Architectural Constraints

### 3.1 Provider Dependency

**Constraint:**  
System depends on external blockchain data providers (Alchemy, Etherscan, TronGrid).

**Implications:**
- Rate limits apply (free tier: limited requests/month)
- Provider downtime affects system availability
- Provider API changes require adapter updates
- Provider cost increases if scaling beyond free tier

**Mitigation:**
- Provider abstraction allows swapping
- Multiple provider support (primary + fallback)
- Caching reduces requests
- Graceful degradation on provider failure

**Known Risk:**
- If provider sunsets API, adapter rewrite needed
- Acceptable risk (standard industry practice)

---

### 3.2 No Self-Hosted Blockchain Nodes

**Constraint:**  
MVP does NOT run self-hosted Ethereum/TRON nodes.

**Implications:**
- No full control over data access
- No ability to query arbitrary historical data without provider limits
- Cost to scale beyond free tier

**Rationale:**
- Running full nodes requires 2TB+ storage, significant infrastructure
- Syncing takes days/weeks
- Maintenance burden
- Out of MVP scope

**Future Enhancement:**
- Phase 10+: Optional self-hosted node support for high-volume users

---

### 3.3 No Real-Time Graph Updates

**Constraint:**  
Transaction graph updates asynchronously, not in true real-time.

**Implications:**
- Trace initiated → background job runs → graph ready (seconds to minutes)
- Frontend polls for updates or receives completion notification
- Not live-streaming graph expansion

**Rationale:**
- Multi-hop tracing takes time (provider API calls)
- Background jobs more scalable than blocking requests
- Good enough for investigation workflow

**Future Enhancement:**
- Phase 9: Websocket updates for live graph expansion visualization

---

### 3.4 Entity Registry Curation

**Constraint:**  
Entity registry is manually curated, not automatically discovered.

**Implications:**
- Known entities must be added to database
- Not all exchanges/VASPs will be in registry initially
- Attribution limited to known entities
- Clustering is basic (not advanced proprietary algorithms)

**Rationale:**
- Automated global clustering requires massive infrastructure
- Manual curation sufficient for MVP
- Demonstrate workflow with known entities

**Future Enhancement:**
- Phase 9: Automated clustering algorithms
- Phase 11: Integration with commercial intelligence feeds (if authorized)

---

## 4. Phase 0 Limitations

### 4.1 No Implementation Yet

**Current State:**  
Phase 0 is documentation only.

**What exists:**
- Architecture documents ✅
- Project context ✅
- Agent team structure ✅

**What does NOT exist:**
- No database schema (yet)
- No API routes (yet)
- No blockchain adapters (yet)
- No frontend UI (yet)
- No working code (yet)

**This is expected. Phase 0 is foundation.**

---

### 4.2 No Performance Benchmarks

**Current State:**  
No performance testing conducted (Phase 7).

**Unknown:**
- Actual trace time for 5-hop Ethereum trace
- Database query performance at scale
- Graph generation performance with 10,000+ nodes
- Frontend rendering performance with large graphs

**Mitigation:**
- Performance testing scheduled for Phase 7
- Optimization deferred until bottlenecks identified

---

### 4.3 No Security Audit

**Current State:**  
Security model documented, but not audited (Phase 7).

**Unknown:**
- Actual vulnerabilities
- Penetration test results
- Real-world attack surface

**Mitigation:**
- Security review gates at each phase
- Security Engineer activated in Phase 7
- Security audit before production deployment

---

## 5. Data Limitations

### 5.1 Historical Data Availability

**Limitation:**  
Provider historical data availability varies.

**Implications:**
- Very old transactions may be unavailable
- Archive node access may be limited (free tier)
- Some chains have limited history

**Mitigation:**
- Use providers with archive node access (Alchemy has archive)
- Handle DATA_INCOMPLETE error states
- Display data availability status to investigator

---

### 5.2 Demo Data is Synthetic

**Limitation:**  
MVP includes demo investigations with synthetic/curated data.

**What this means:**
- Demo cases are NOT real investigations
- Demo wallet addresses may be curated for demonstration
- Demo VASP attributions may be manually assigned
- Clearly labeled as DEMO

**Rationale:**
- Cannot use real case data without authorization
- Demo data demonstrates workflow

**Important:**  
Demo data MUST be clearly separated from production cases (is_demo flag).

---

### 5.3 No PII Collection (Intentional)

**Limitation:**  
System does NOT collect victim personally identifiable information.

**What this means:**
- Case metadata is wallet address, fraud type, amount only
- No victim names, contact info, identifying details
- Investigator identity minimal (email, role only)

**Rationale:**
- Privacy by design
- Minimize PII exposure
- Blockchain addresses are public data

**This is NOT a limitation to fix. This is intentional design.**

---

## 6. User Experience Limitations

### 6.1 Desktop-First UI

**Limitation:**  
UI optimized for desktop, acceptable on mobile.

**Implications:**
- Graph visualization best on large screens
- Complex investigation workflows desktop-focused
- Mobile experience not primary target

**Rationale:**
- Investigators use desktops
- Graph visualization requires screen real estate

**Future Enhancement:**
- Phase 10+: Mobile app for case review (view-only)

---

### 6.2 No Multi-Language Support

**Limitation:**  
MVP is English-only.

**Implications:**
- UI text in English
- API responses in English
- Reports in English

**Future Enhancement:**
- Phase 10+: Internationalization (i18n)

---

### 6.3 Single Investigator Per Case

**Limitation:**  
MVP assumes one investigator per case.

**Implications:**
- No collaboration features
- No case sharing
- No team workspaces
- No access control beyond case ownership

**Future Enhancement:**
- Phase 10: Multi-investigator collaboration

---

## 7. Technical Debt (Acceptable for MVP)

### 7.1 No Advanced Caching

**Current State:**  
Basic caching strategy (immutable blockchain data only).

**Future Enhancement:**
- Redis for distributed caching
- Cache warming strategies
- Advanced cache invalidation

---

### 7.2 No Load Balancing

**Current State:**  
Single backend instance (MVP deployment).

**Future Enhancement:**
- Load balancer for multiple backend instances
- Horizontal scaling

---

### 7.3 No Automated Backups (MVP)

**Current State:**  
Supabase automated daily backups only.

**Future Enhancement:**
- Custom backup strategies
- Point-in-time recovery
- Backup testing

---

### 7.4 No Observability Platform

**Current State:**  
Basic logging only.

**Future Enhancement:**
- Centralized logging (e.g., Datadog, New Relic)
- APM (Application Performance Monitoring)
- Alerting platform
- Metrics dashboard

---

## 8. Future Enhancement Candidates

### 8.1 High Priority (Post-MVP)

**Multi-Chain Support:**
- TRON, Solana, Bitcoin adapters

**Advanced Patterns:**
- DeFi protocol interaction detection
- NFT transaction analysis
- Smart contract interaction patterns

**Collaboration:**
- Multi-investigator case sharing
- Team workspaces
- Role-based access control (Admin, Investigator, Viewer)

**Performance:**
- Real-time graph updates
- WebSocket streaming
- Advanced caching

---

### 8.2 Medium Priority

**Integrations:**
- Authorized LEA system integration
- Exchange API partnerships (KYC data if authorized)
- External intelligence feeds

**Intelligence:**
- Advanced clustering algorithms
- Machine learning pattern detection (as enhancement layer)
- Behavioral analysis

**Reporting:**
- Scheduled reports
- Automated report distribution
- Multi-case comparison reports

---

### 8.3 Lower Priority

**Mobile:**
- Mobile app (view-only)
- Mobile-optimized graph visualization

**Localization:**
- Multi-language support (i18n)

**Automation:**
- Automated case creation (if integrated with NCRP)
- Automated evidence tagging
- Automated report scheduling

---

## 9. What LedgerLens MVP IS

✅ Blockchain intelligence workstation  
✅ Fund-flow tracing tool  
✅ Explainable risk scoring  
✅ VASP attribution (with confidence)  
✅ Evidence preservation  
✅ Investigation report generation  
✅ Human-in-the-loop workflow  
✅ Ethereum support (primary)  
✅ Deterministic, explainable algorithms  
✅ Provider-agnostic architecture  
✅ Credible MVP demonstration  

---

## 10. What LedgerLens MVP IS NOT

❌ Commercial Chainalysis replacement  
❌ Legally definitive attribution system  
❌ Real-time mempool monitor  
❌ All-blockchain support (simultaneously)  
❌ Autonomous investigator (replaces humans)  
❌ Guaranteed accuracy system  
❌ Self-hosted blockchain node infrastructure  
❌ Officially integrated with NCRP/LEA/exchanges (unless authorized)  
❌ Machine learning black-box  
❌ Production-scale commercial platform (yet)  

---

## 11. Acceptance of Limitations

These limitations are **intentional scope decisions**, not failures.

**MVP Purpose:**
- Demonstrate core workflow
- Prove architectural approach
- Validate explainability principle
- Foundation for future enhancement

**MVP Success Criteria:**
- Investigator can trace funds from victim-reported wallet ✅
- Investigator sees transaction graph ✅
- Investigator sees VASP attribution with confidence ✅
- Investigator understands WHY wallet is suspicious (explainable) ✅
- Investigator can generate investigation report ✅
- System handles provider failures gracefully ✅

**If MVP meets success criteria, limitations are acceptable.**

---

## Document Status

**Phase 0:** Known limitations documented ✅  
**Status:** Scope boundaries clarified  
**Approval Required:** MASTER / CTO  
**Dependencies:** PROJECT_BRIEF.md, ROADMAP.md, ARCHITECTURE.md

---

**Key Principle:**  
Quality > Quantity  
Evidence > Assumptions  
Architecture > Hacks  
Explainability > Black-box claims  
Verification > Confidence  
Human investigator > Autonomous legal conclusion
