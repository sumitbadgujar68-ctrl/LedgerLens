# LedgerLens — Phase 3 UI/UX Design Specification (Final)
**Forensic Blockchain Investigation Workstation for Cyber-Fraud Inquiries**

**Document Version:** 2.1.0 (Final Workstation Edition)  
**Phase:** PHASE 3 — INVESTIGATION UI  
**Target User:** Cyber-Fraud Investigators, Law-Enforcement Analysts, Financial Intelligence Specialists  
**Core Ethos:** *"Observe the blockchain evidence, investigate the flow, preserve the evidence."*  
**Status:** FINAL ✅

---

## 1. Primary Design Vision & Core Principles

LedgerLens Phase 3 is a **forensic cryptocurrency investigation workstation**, not a generic SaaS admin dashboard, fintech product, or sci-fi crypto terminal. It is built to support law-enforcement officers and cyber-fraud analysts in discovering where stolen funds moved, how many hops were involved, and what evidence must be preserved for subpoenas and prosecution.

### Visual Workstation Prototype

![Investigation Workspace — Fund-Flow Graph, Forensic Ledger & Inspector](C:\Users\Sumit\.gemini\antigravity-ide\brain\e5c4da9b-0a23-48b8-b9bc-5a722b6a21a0\refined_investigation_workspace_1790142067139.jpg)

![Investigator Dashboard — Case Dispatch, Scannable Table & Demo Telemetry](C:\Users\Sumit\.gemini\antigravity-ide\brain\e5c4da9b-0a23-48b8-b9bc-5a722b6a21a0\refined_investigator_dashboard_1790142038856.jpg)

![Forensic Transaction Detail Drawer — Cryptographic Provenance & Evidence Actions](C:\Users\Sumit\.gemini\antigravity-ide\brain\e5c4da9b-0a23-48b8-b9bc-5a722b6a21a0\refined_transaction_drawer_1790142123678.jpg)

### Core Workstation Principles

1. **Analytical & Restrained Aesthetic:**
   - Deep near-black canvas (`#090B10`) with subtle slate surfaces (`#121620`, `#161B26`) and crisp 1px borders (`#1F2637`).
   - Zero neon glow, gratuitous gradients, or consumer SaaS clutter. Every pixel communicates forensic information.
2. **Clear Distinction: On-Chain Facts vs. Future Intelligence:**
   - Verifiable on-chain realities (transaction hashes, block numbers, gas fees, timestamps) are strictly delineated from investigator notes.
   - **Phase Boundary Enforcement:** Consciously excludes mock VASP attribution, exchange cluster claims, AI risk scoring, and cross-chain bridging until Phase 4 and Phase 5 backend services are activated.
3. **The Investigation Workspace is the Hero:**
   - The Dashboard serves purely as an efficient launchpad. The Investigation Workspace is the actual core product where the investigator spends 90% of their operational time.
   - The multi-hop Fund-Flow Graph visually dominates the screen (~70% width), supported by a persistent right-side Inspector and a tabbed bottom dock.
4. **Truthful State-Based Progress (No Fake Percentages):**
   - Trace execution reflects real backend states: `1. Querying Provider` → `2. Fetching Transfers` → `3. Normalizing Transactions` → `4. Expanding Graph` → `5. Finalizing Trace`.
5. **Direct Backend API Mapping:**
   - The frontend strictly consumes existing FastAPI endpoints (`/api/v1/cases`, `/api/v1/cases/{case_id}/traces`). No blockchain extraction or RPC logic lives in client-side code.

---

## 2. Global Design System Foundations

### 2.1 Canonical MVP Navigation Rail

The sidebar navigation is strictly locked to three primary destinations, ensuring a compact, uncluttered rail that does not compete with the investigation workspace:

```
┌────────────────────────────────────────────────────────────┐
│ LEDGERLENS [Radar Glyph]                                   │
├────────────────────────────────────────────────────────────┤
│ [📁] Investigations   ──> Active case dispatch & workspaces│
│ [⚖️] Evidence         ──> Pinned artifacts & audit custody  │
│ [⚙️] Settings         ──> Provider config & node latency   │
├────────────────────────────────────────────────────────────┤
│ [➜] Log out          ──> Investigator session termination │
└────────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **No Top-Level "Reports" Route:** In accordance with investigative workflows, report generation and court brief exporting are contextual forensic actions located directly inside the Investigation Workspace (`[Export Brief]`) and the Evidence Panel (`[Export Court Package]`). Reports are never a standalone top-level navigation destination.

---

### 2.2 Color Tokens & Theming

```css
/* Surface Palette (Tactical Dark Default) */
--surface-canvas:      #090B10; /* Viewport canvas background */
--surface-sidebar:     #0D1017; /* Left navigation rail */
--surface-card:        #121620; /* Primary card / panel backgrounds */
--surface-inspector:   #161B26; /* Persistent right-side inspector */
--surface-dock:        #0E1119; /* Bottom ledger / timeline dock */
--surface-elevated:    #1C2333; /* Flyouts, dropdowns, hovered nodes */
--surface-overlay:     rgba(9, 11, 16, 0.85); /* Modal backdrops */

/* Structural Borders & Dividers */
--border-subtle:       #1F2637; /* Structural dividers, table borders */
--border-strong:       #2D374D; /* Active inputs, selected cards */
--border-highlight:    #2563EB; /* Focus rings, selected nodes, active paths */

/* Typography Tokens */
--text-primary:        #F8FAFC; /* High-contrast headers, values, hashes */
--text-secondary:      #94A3B8; /* Labels, metadata, hop counters */
--text-muted:          #64748B; /* Secondary timestamps, disabled state */
--text-mono:           #CBD5E1; /* Addresses, blocks, raw data */

/* Status & Accents */
--accent-primary:      #2563EB; /* Primary actions (Start Trace, Create Case) */
--accent-primary-hover:#1D4ED8;
--status-active:       #10B981; /* Confirmed on-chain, healthy connection */
--status-warning:      #F59E0B; /* Provider rate limit, dust-filtered branches, cycles */
--status-danger:       #EF4444; /* Root suspect wallet, failed trace */
--status-neutral:      #64748B; /* Archived case, closed trace */
```

---

### 2.3 Two-Layer Typography System

To maintain maximum legibility and scan speed, the interface separates UI narrative from cryptographic data:
- **Layer 1 — UI & Prose:** `Inter`, `-apple-system`, `sans-serif` (headers, labels, buttons, notes).
- **Layer 2 — Blockchain Data:** `JetBrains Mono`, `ui-monospace`, `monospace` (addresses, hashes, block numbers, asset amounts).

| Token | Family | Size | Weight | Line Height | Tracking | Usage |
|---|---|---|---|---|---|---|
| `display-lg` | Inter | 20px | 600 | 28px | -0.015em | Case Command Bar, Screen Titles |
| `header-md` | Inter | 14px | 600 | 20px | -0.01em | Panel & Section Headers |
| `body-sm` | Inter | 13px | 400 | 18px | Normal | Descriptions, notes, table rows |
| `micro-caps` | Inter | 10px | 700 | 14px | +0.05em | Badges, status pills, hop tags (uppercase) |
| `mono-code` | JetBrains Mono | 12px | 400 | 16px | 0 | Addresses (`0x...`), tx hashes |
| `mono-num` | JetBrains Mono | 13px | 500 | 18px | -0.01em | Asset amounts (`14.5000 ETH`), block numbers |

---

### 2.4 Hop Encoding & Graph Node Taxonomy

```
[HOP 0 - ROOT SUSPECT]  ──> Crimson Red    (#EF4444 / Border: #EF4444 / Tag: "ROOT SUSPECT")
[HOP 1 - DIRECT OUT]    ──> Amber Gold     (#F59E0B / Border: #F59E0B / Tag: "HOP 1")
[HOP 2 - SECONDARY HOP] ──> Electric Indigo(#6366F1 / Border: #6366F1 / Tag: "HOP 2")
[HOP 3 - DEEP HOP]      ──> Cyan Teal      (#06B6D4 / Border: #06B6D4 / Tag: "HOP 3")
[HOP 4+ PERIPHERY]      ──> Muted Slate    (#64748B / Border: #64748B / Tag: "HOP 4+")
[CYCLE / LOOP DETECTED] ──> Dashed Amber   (#F59E0B / Dash: 4 2 / Tag: "CYCLE DETECTED")
```

---

## 3. Screen Specifications (All 7 Screens)

---

### Screen 1: Investigator Dashboard (`/cases`)

The launchpad for managing cyber-fraud investigations. Replaces bulky KPI cards with low-profile telemetry and emphasizes an ultra-scannable case ledger.

#### Layout Specification
- **Navigation Rail:** `Investigations` (active), `Evidence`, `Settings`.
- **Top Bar:** Quick Search (`Ctrl+K`) supporting instant queries by Case Number, Suspect Address, or Incident Title.
- **Quick Filters:** Filter pills for `Active`, `Under Investigation`, `Closed`, `High Activity`, and `Recent Trace`.
- **Primary Action:** `[+ New Investigation]` prominent button on top right.
- **Compact Telemetry Ribbon (STRICTLY DEMO LABELED):**
  - `DEMO TELEMETRY`: `Active Cases: 14` · `Multi-Hop Traces: 48` · `Preserved Evidence: 82` · `Provider: Alchemy (Ethereum Mainnet Active)`
- **Forensic Case Ledger Table:**
  - `CASE IDENTIFIER`: Monospaced blue link (`DEMO-INV-001`).
  - `INCIDENT REFERENCE`: Human-readable title (`Synthetic Pig Butchering Scam`).
  - `REPORTED WALLET`: Truncated monospace address (`0x71C8...d557`) with one-click copy icon.
  - `REPORTED LOSS`: Monospaced amount (`25.40 ETH` or `25,000 USDT`).
  - `STATUS`: Subtle pill badge (`Active` in green, `Under Investigation` in amber, `Closed` in slate).
  - `LAST TRACE`: Relative timestamp (`12m ago`).
  - `ACTION`: Direct link `[Open Workspace]`.

```
+---------------------------------------------------------------------------------------------------+
| LEDGERLENS | Investigations > Dispatch Dashboard                                 [Ctrl+K Search] |
+------------+--------------------------------------------------------------------------------------+
| [Rail]     | DEMO TELEMETRY:                                                                      |
|            | [Active Cases: 14] [Multi-Hop Traces: 48] [Preserved Evidence: 82] [Provider: Alchemy] |
| [Investig] |                                                                                      |
| [Evidence] | [ Forensic Search: Case #, Wallet Address, Incident Title...     ] [+ New Investigation] |
| [Settings] | Filters: [Active] [Under Investigation] [Closed] [High Activity] [Recent Trace]     |
|            +--------------------------------------------------------------------------------------+
|            | CASE IDENTIFIER  | INCIDENT REFERENCE          | REPORTED WALLET      | AMOUNT    | ACT|
|            |------------------+-----------------------------+----------------------+-----------+----|
|            | DEMO-INV-001     | Synthetic Pig Butchering    | 0x71C8...d557 [📋]   | 25.40 ETH | Open
|            | DEMO-INV-002     | Synthetic Task Scam         | 0x388C...6b42 [📋]   | 12,500 U  | Open
|            | DEMO-INV-003     | Synthetic Ransomware Lock   | 0xdAC1...1EC7 [📋]   | 8.10 ETH  | Open
|            +--------------------------------------------------------------------------------------+
|            | Showing 1-20 of 48 cases                                                             |
+------------+--------------------------------------------------------------------------------------+
```

---

### Screen 2: New Investigation Intake (`/cases/new`)

A tactical modal/intake form that enforces strict validation before writing to the database via `POST /api/v1/cases`.

- **Field 1: Case Identity:** Title / incident reference (1–500 chars).
- **Field 2: Blockchain & Suspect Address:**
  - Blockchain: Dropdown locked to `Ethereum (Mainnet)`.
  - Suspect Wallet Address: Full 42-character input with real-time checksum validation (`0x[a-fA-F0-9]{40}`). Displays green checkmark indicator when valid.
  - Initial Tx Hash (Optional): Triggers starting node lookup.
- **Field 3: Fraud Type & Loss:**
  - Fraud Type: Dropdown matching backend enum: `investment_scam`, `ransomware`, `sextortion`, `phishing`, `task_based_fraud`, `darknet`, `other`.
  - Reported Loss Amount: Decimal input with asset token selector (`ETH`, `USDT`, `USDC`).
- **Field 4: Investigator Memorandum:** Initial narrative summary stored in `investigator_notes`.
- **Submission:** Invokes `POST /api/v1/cases` and redirects immediately to the generated Workspace (`/cases/:case_id`).

---

### Screen 3: Investigation Workspace (`/cases/:id`) — [HERO PRODUCT SCREEN]

The core workstation where the investigator conducts analysis. Visually dominated by the Fund-Flow Graph, with a persistent right Inspector and a bottom investigation dock.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ CASE CONTEXT / COMMAND BAR:                                                            │
│ CASE: DEMO-INV-001 · Synthetic Investment Fraud · Wallet: 0x71C8...d557 · Status: Active│
├────────────────────────────────────────────────────────────────────────────────────────┤
│ TRACE CONTROLS (POST /cases/{id}/traces)                │ TRACE EXECUTION STATUS       │
│ Direction: [Outbound v] Hops: [ 3 ] Branch: [ 25 ]      │ Status: COMPLETED            │
│ Min Amount: [ 0.05 ETH ]   [ ▶ Start Trace ]            │ 18 Wallets · 34 Txs · Alchemy│
├─────────────────────────────────────────┬───────────────┴──────────────────────────────┤
│                                         │ SELECTED WALLET INSPECTOR                    │
│                                         │ 0x8290...3a19 [📋]  [↗ Etherscan]            │
│                                         │ Hop: Hop 1 Intermediary                      │
│                                         ├──────────────────────────────────────────────┤
│          FUND-FLOW GRAPH                │ ACTIVITY SUMMARY                             │
│          (Visually Dominant)            │ Inflow:  14.5000 ETH (2 transfers)           │
│                                         │ Outflow: 14.4920 ETH (Rapid Forwarding)      │
│   (Root Suspect)                        │ Dwell:   6 minutes                           │
│        0x71C8...d557                    ├──────────────────────────────────────────────┤
│              │                          │ FLOW COUNTERPARTIES                          │
│     14.50 ETH│10.90 ETH                 │ From: 0x71C8...d557 (Hop 0)                  │
│        ▼     │    ▼                     │ To:   0x9920...11e3 (Hop 2)                  │
│     (Hop 1)  │  (Hop 1)                 │ To:   0x3a42...99f1 (Hop 2)                  │
│   0x8290...  │ 0x3a42...                ├──────────────────────────────────────────────┤
│        │                                │ ACTIONS                                      │
│        ▼                                │ [ + Pin Wallet to Evidence ]                 │
│     (Hop 2)                             │ [ View Direct Transactions ]                 │
│   0x9920...                             │ [ Add Investigator Note ]                    │
├─────────────────────────────────────────┴──────────────────────────────────────────────┤
│ BOTTOM DOCK: [ Transactions (34) ]  [ Timeline ]  [ Evidence (4) ]  [ Notes ]          │
│ Hash: 0x4f89... | From: 0x71C8... | To: 0x8290... | Amount: 14.50 ETH | 14:35 UTC [Pin]│
│ Hash: 0x91cc... | From: 0x8290... | To: 0x9920... | Amount: 10.00 ETH | 14:41 UTC [Pin]│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Screen 4: Fund-Flow Graph Canvas (Deep Dive)

The visual identity of LedgerLens:
- **Hierarchical Hop Layout:** Left-to-right columnar alignment (Hop 0 on left → Hop 1 → Hop 2 → Hop 3).
- **Node Anatomy:**
  - Header: Hop badge (`ROOT`, `HOP 1`, `HOP 2`) with distinct color tag.
  - Center: Truncated address in JetBrains Mono (`0x71C8...d557`) with copy icon on hover.
  - Sub-label: Throughput volume chip (`14.50 ETH IN / 14.49 ETH OUT`).
  - Selection State: Solid 2px blue ring (`#2563EB`) with path highlighting.
- **Edge Routing & Labels:**
  - Directed curves with clear directional arrowheads.
  - Value pill centered on edge (`14.50 ETH`, `25,000 USDT`).
  - Active path edges are illuminated in solid blue; unselected paths drop to 40% opacity.
- **Cycle & Loop Highlighting:** Circular transfers returning to an earlier hop are rendered with dashed amber strokes (`#F59E0B`) and labeled `CYCLE DETECTED`.
- **Canvas Toolbox:** Floating low-profile controls for `Zoom In (+)`, `Zoom Out (-)`, `Fit View (⛶)`, and `Layout (Hierarchical / Clustered)`.

---

### Screen 5: Forensic Transaction Detail Drawer

A deep inspection flyout drawer opening when an edge or transaction row is selected:
- **Transaction Hash:** Full 66-character hash in light blue monospace with one-click copy and Etherscan link.
- **Blockchain Provenance:** Block number (`18,234,567`), block timestamp (`2026-09-22 14:35:12 UTC`), provider source (`Alchemy v2 API`), confirmation status (`Confirmed on-chain`).
- **Asset & Value:** Exact amount in monospace (`25,000.00000000 USDT`), asset type (`ERC-20 Token`), token contract address (`0xdAC1...1EC7`).
- **Counterparties:** Formatted From/To rows with hop distance indicators.
- **Gas & Network Fees:** Gas units used (`48,210`) and total fee paid (`0.0034 ETH`).
- **Evidentiary Action:** `[+ Pin Transaction to Evidence]` with immediate inclusion in case brief.

---

### Screen 6: Wallet Detail Dossier

Granular behavioral dossier for any selected node in the graph:
- **Address & Checksum:** Full verified 42-character string.
- **Hop Distance:** Distance from root suspect (`Hop 1 Intermediary`).
- **Activity Summary:** Cumulative inbound and outbound volume within this trace.
- **Dwell Time:** Time elapsed between inbound receipt and outbound transfer (e.g. `6 minutes` indicating rapid forwarding).
- **Direct Counterparty Matrix:** Grouped list of adjacent senders and recipients.
- **Action:** `[+ Pin Wallet to Evidence]` and `[Add Note]`.

---

### Screen 7: Evidence & Notes Panel (Bottom Dock / Flyout)

The evidentiary repository ensuring chain of custody and court export:
- **Pinned Artifacts:** Categorized list of flagged wallets and transactions with timestamped capture dates and investigator notes.
- **Investigation Working Log:** Persistent notes area that syncs with `cases.investigator_notes` via `PUT /api/v1/cases/{case_id}`.
- **Standardized Export:** One-click generation of court-ready PDF briefs and machine-readable JSON/CSV forensic packages (`[Export Brief]`).

---

## 4. Truthful Trace Execution Progress Model

LedgerLens does not use simulated percentages. The trace progress indicator maps 1:1 to real backend execution stages:

```
[ STAGE 1: QUERYING PROVIDER ] ───> Dispatches Alchemy transfer requests via backend adapter
       │
[ STAGE 2: FETCHING TRANSFERS ] ───> Paginating transfer records (Page N of M)
       │
[ STAGE 3: NORMALIZING TXS ]   ───> Canonical transaction normalization & Decimal conversion
       │
[ STAGE 4: EXPANDING GRAPH ]   ───> Constructing BFS multi-hop adjacency nodes and edges
       │
[ STAGE 5: TRACE FINALIZED ]   ───> Graph persisted in DB, rendered on canvas
```

---

## 5. Actionable Error & Empty States

| Trigger / Context | State | Actionable Message & Visual Treatment |
|---|---|---|
| **Empty Case Ledger** | Empty | Centered radar graphic: *"No investigations registered. Click '+ New Investigation' to begin an inquiry."* |
| **Provider Rate Limit** | Warning | Amber banner: *"Alchemy API rate limit reached. Trace preserved with 18 of 24 transfers. Consider narrowing time range."* |
| **Provider Unavailable** | Error | Crimson banner: *"Blockchain data provider temporarily unavailable. Please verify backend Alchemy configuration."* |
| **Invalid Address** | Input Error | Inline red text below input: *"Invalid Ethereum address checksum. Ensure address begins with '0x' and contains 40 hex characters."* |
| **Dust Filter Zero Results**| Filter Notice | Tactical callout: *"Zero transfers matched criteria (Min Amount: 0.05 ETH). Lower dust filter to display micro-transfers."* |
| **Partial Trace Data** | Notice | Amber badge: *"Trace completed with partial data: branch cap (25) reached on Hop 2."* |

---

## 6. Future Intelligence Extensibility (Phases 4 & 5)

The interface reserves structured visual zones for future modules without faking data in Phase 3:

```
┌────────────────────────────────────────────────────────────┐
│ [TAB: ENTITY ATTRIBUTION - COMING IN PHASE 4]             │
│ VASP identification, exchange cluster matching & heuristics│
├────────────────────────────────────────────────────────────┤
│ [TAB: RISK ANALYSIS - COMING IN PHASE 4]                   │
│ Explainable typology scoring, peel-chain & mixer detection │
├────────────────────────────────────────────────────────────┤
│ [TAB: AI INVESTIGATION COPILOT - COMING IN PHASE 5]        │
│ Grounded LLM reasoning, evidence synthesis & natural query │
└────────────────────────────────────────────────────────────┘
```

---

## 7. Frontend Architecture & API Integration Mapping

```
┌────────────────────────────────────────────────────────────┐
│                    PHASE 3 FRONTEND                        │
│             (React / TypeScript / Tailwind CSS)            │
├───────────────────────────────┬────────────────────────────┤
│ Workstation Components:       │ State & Integration:       │
│ - InvestigatorDashboardTable  │ - CaseApiClient            │
│ - NewInvestigationModal       │ - TraceApiClient           │
│ - InvestigationWorkspace      │ - GraphRenderEngine (SVG)  │
│ - FundFlowGraphCanvas         │ - EvidenceStore (Zustand)  │
│ - ForensicTransactionDrawer   │ - ActiveCaseContext        │
│ - WalletDossierInspector      │                            │
│ - EvidenceNotesDock           │                            │
└───────────────────────────────┴────────────────────────────┘
                                │ HTTP REST JSON (Async)
                                ▼
┌────────────────────────────────────────────────────────────┐
│                  FASTAPI BACKEND ENDPOINTS                 │
│                     (Verified in Phase 1 & 2)              │
├────────────────────────────────────────────────────────────┤
│ • POST /api/v1/cases                  (Case Intake)        │
│ • GET  /api/v1/cases                  (List Cases)         │
│ • GET  /api/v1/cases/{case_id}        (Case Details)       │
│ • PUT  /api/v1/cases/{case_id}        (Update Notes/Status)│
│ • POST /api/v1/cases/{id}/traces      (Execute BFS Trace)  │
│ • GET  /api/v1/cases/{id}/traces      (List Case Traces)   │
│ • GET  /api/v1/cases/{id}/traces/{t}  (Retrieve Subgraph)  │
└────────────────────────────────────────────────────────────┘
```

---

## 8. Final Consistency Verification

1. **Sidebar Navigation:** Strictly aligned across specification and mockups to three MVP items:
   - `Investigations` (`/cases`)
   - `Evidence` (`/evidence`)
   - `Settings` (`/settings`)
   - **Reports Exclusion:** Confirmed that `Reports` is NOT a primary navigation item. Report generation remains an action within the Investigation Workspace (`[Export Brief]`) and the Evidence Panel (`[Export Court Package]`).
2. **DEMO TELEMETRY Labels:** Strictly preserved on all synthetic telemetry chips and fictional case examples (`DEMO-INV-001`, `Synthetic Pig Butchering Scam`).
3. **Phase Boundaries:** Preserves 100% adherence to Phase 3 scope with zero premature intelligence.

**Phase 3 UI/UX Specification is now FINAL.**
