# LedgerLens — Blockchain Forensic Investigation Workstation

LedgerLens is a real-time crypto fraud attribution system designed for forensic analysts and security researchers. It provides a comprehensive workstation to trace multi-hop wallet transactions, generate interactive fund-flow graphs, and score wallet risk profiles using advanced heuristic engines powered by Alchemy.

## 🚀 Features

*   **Real-time Fund Tracking**: Trace multi-hop transactions across supported blockchain networks.
*   **Interactive Fund-Flow Graphs**: Visualize complex transaction webs with a node-based interface powered by React Flow.
*   **Risk Scoring**: Evaluate entity risk profiles utilizing heuristic engines.
*   **Forensic Investigation Workspace**: A dedicated environment for analysts to compile dockets, analyze data, and generate provenance reports.
*   **Zero-Fabrication Guarantee**: Telemetry is strictly provenance-backed to ensure forensic integrity.

## 🛠️ Tech Stack

*   **Frontend**: React, Vite, TypeScript, React Flow, Tailwind CSS, Zustand, TanStack Query
*   **Backend**: FastAPI, Python, Pydantic, pytest
*   **Database**: Supabase (PostgreSQL)
*   **Blockchain Integration**: Alchemy API

## 📦 Deployment Status

*   **Frontend**: Configured and ready for Vercel deployment.
*   **Backend**: Production-ready FastAPI application.

## 🧪 Testing and Quality Assurance

LedgerLens maintains high forensic standards:
*   **Backend**: Comprehensive `pytest` suite ensuring strict schema validation and error resilience.
*   **Frontend**: Validated with Vitest and strict TypeScript compiler checks (`noUnusedLocals: true`).

---
*LedgerLens — Enforcing Forensic Purity in Web3.*
