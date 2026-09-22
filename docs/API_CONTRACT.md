# LedgerLens API Contract

**Last Updated:** 2026-09-22  
**Phase:** PHASE 0 — FOUNDATION  
**Status:** Initial API Contract (Conceptual)

---

## 1. Overview

This document defines the conceptual API contract between the LedgerLens backend (FastAPI) and frontend (React/Next.js). This is a Phase 0 architectural specification, not a complete implementation guide.

The API follows RESTful principles with JSON request/response format, versioned endpoints, and consistent error handling.

---

## 2. API Design Philosophy

### 2.1 Core Principles

**RESTful Design:**
- Resources identified by URLs
- HTTP methods convey intent (GET, POST, PUT, DELETE)
- Stateless requests
- Consistent resource naming

**JSON-First:**
- All request bodies and responses use JSON
- ISO 8601 datetime format
- Decimal amounts as strings to preserve precision

**Versioned:**
- API versioned via URL path (`/api/v1/...`)
- Allows backward compatibility

**Consistent:**
- Predictable response structure
- Standard error format
- Pagination pattern
- Filtering/sorting conventions

**Secure:**
- Authentication required for all endpoints (except health check)
- Authorization enforced based on investigator role
- Input validation on all requests

---

### 2.2 Base URL

```
Development: http://localhost:8000/api/v1
Production: https://api.ledgerlens.example.com/api/v1
```

---

## 3. Authentication

### 3.1 Authentication Approach

**Method:** JWT (JSON Web Token) bearer authentication

**Flow:**
1. Investigator logs in with credentials
2. Backend returns JWT access token
3. Frontend includes token in `Authorization` header for subsequent requests
4. Token expires after N hours (configurable)

**Request Header:**
```
Authorization: Bearer <jwt_token>
```

### 3.2 Authentication Endpoints

**POST /auth/login**
```json
Request:
{
  "username": "investigator@agency.gov",
  "password": "securepassword"
}

Response (200 OK):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "investigator": {
    "investigator_id": "uuid",
    "username": "investigator@agency.gov",
    "full_name": "Jane Investigator",
    "role": "investigator"
  }
}

Response (401 Unauthorized):
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid username or password"
  }
}
```

**POST /auth/logout**
```json
Request: (empty body, requires Authorization header)

Response (200 OK):
{
  "message": "Successfully logged out"
}
```

**GET /auth/me**
```json
Response (200 OK):
{
  "investigator_id": "uuid",
  "username": "investigator@agency.gov",
  "full_name": "Jane Investigator",
  "role": "investigator",
  "created_at": "2026-09-01T10:00:00Z",
  "last_login": "2026-09-22T13:45:00Z"
}
```

---

## 4. Resource Endpoints

### 4.1 Cases

**POST /cases**  
Create a new investigation case.

```json
Request:
{
  "title": "Investment Scam - Victim ID 4521",
  "reported_wallet_address": "0xABC123...",
  "reported_transaction_hash": "0xDEF456..." (optional),
  "blockchain": "ethereum",
  "fraud_type": "investment_scam",
  "reported_amount": "5000.00",
  "reported_asset": "USDT",
  "reported_date": "2026-09-20T14:23:11Z",
  "investigator_notes": "Victim reported loss after fake investment platform"
}

Response (201 Created):
{
  "case_id": "uuid",
  "case_number": "CASE-2026-001234",
  "status": "active",
  "created_at": "2026-09-22T13:45:00Z",
  "trace_job_id": "uuid" (background job ID)
}
```

**GET /cases**  
List all cases for current investigator.

```json
Query Parameters:
- status: active|closed|archived (optional)
- fraud_type: investment_scam|ransomware|... (optional)
- blockchain: ethereum|tron (optional)
- page: 1 (default)
- per_page: 20 (default)

Response (200 OK):
{
  "cases": [
    {
      "case_id": "uuid",
      "case_number": "CASE-2026-001234",
      "title": "Investment Scam - Victim ID 4521",
      "reported_wallet_address": "0xABC123...",
      "blockchain": "ethereum",
      "fraud_type": "investment_scam",
      "status": "active",
      "created_at": "2026-09-22T13:45:00Z",
      "updated_at": "2026-09-22T14:10:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "total_pages": 3
  }
}
```

**GET /cases/{case_id}**  
Retrieve detailed case information.

```json
Response (200 OK):
{
  "case_id": "uuid",
  "case_number": "CASE-2026-001234",
  "title": "Investment Scam - Victim ID 4521",
  "reported_wallet_address": "0xABC123...",
  "reported_transaction_hash": "0xDEF456...",
  "blockchain": "ethereum",
  "fraud_type": "investment_scam",
  "reported_amount": "5000.00",
  "reported_asset": "USDT",
  "reported_date": "2026-09-20T14:23:11Z",
  "status": "active",
  "created_at": "2026-09-22T13:45:00Z",
  "updated_at": "2026-09-22T14:10:00Z",
  "investigator_notes": "Victim reported loss after fake investment platform",
  "summary": {
    "wallet_count": 47,
    "transaction_count": 152,
    "total_traced_amount": "4800.00",
    "max_hop_depth": 5,
    "vasp_attributions_count": 2
  }
}
```

**PUT /cases/{case_id}**  
Update case status or notes.

```json
Request:
{
  "status": "closed",
  "investigator_notes": "Case resolved, evidence submitted"
}

Response (200 OK):
{
  "case_id": "uuid",
  "status": "closed",
  "updated_at": "2026-09-22T16:30:00Z"
}
```

---

### 4.2 Wallets

**GET /cases/{case_id}/wallets**  
List all wallets discovered in case.

```json
Query Parameters:
- wallet_type: suspect|intermediary|destination (optional)
- min_hop: 0 (optional)
- max_hop: 5 (optional)
- page: 1
- per_page: 50

Response (200 OK):
{
  "wallets": [
    {
      "wallet_id": "uuid",
      "address": "0xABC123...",
      "blockchain": "ethereum",
      "label": "Initial Suspect Wallet",
      "wallet_type": "suspect",
      "discovered_at_hop": 0,
      "total_received": "5000.00",
      "total_sent": "4800.00",
      "transaction_count": 12,
      "first_seen": "2026-09-20T14:23:11Z",
      "last_activity": "2026-09-21T08:15:43Z",
      "risk_score": {
        "score": 87,
        "category": "high"
      },
      "vasp_attribution": null
    }
  ],
  "pagination": { ... }
}
```

**GET /cases/{case_id}/wallets/{wallet_id}**  
Detailed wallet information.

```json
Response (200 OK):
{
  "wallet_id": "uuid",
  "address": "0xABC123...",
  "blockchain": "ethereum",
  "label": "Initial Suspect Wallet",
  "wallet_type": "suspect",
  "discovered_at_hop": 0,
  "total_received": "5000.00",
  "total_sent": "4800.00",
  "transaction_count": 12,
  "first_seen": "2026-09-20T14:23:11Z",
  "last_activity": "2026-09-21T08:15:43Z",
  "risk_score": {
    "risk_score_id": "uuid",
    "score": 87,
    "risk_category": "high",
    "scoring_version": "v1.0",
    "calculated_at": "2026-09-22T14:00:00Z",
    "factors": [
      {
        "factor_type": "rapid_onward_transfer",
        "weight": 20,
        "evidence": {
          "transaction_hash": "0xDEF456...",
          "time_delta_hours": 1.5
        }
      }
    ]
  },
  "vasp_attribution": {
    "attribution_id": "uuid",
    "candidate_entity": {
      "entity_id": "uuid",
      "name": "Binance",
      "entity_type": "exchange"
    },
    "confidence": 0.82,
    "attribution_method": "cluster_match",
    "attributed_at": "2026-09-22T14:05:00Z"
  },
  "patterns": [
    {
      "pattern_id": "uuid",
      "pattern_type": "peel_chain",
      "confidence": 0.89,
      "detected_at": "2026-09-22T14:03:00Z"
    }
  ]
}
```

---

### 4.3 Transactions

**GET /cases/{case_id}/transactions**  
List all transactions in case.

```json
Query Parameters:
- wallet_address: 0xABC... (optional, filter by wallet)
- min_amount: 100.00 (optional)
- min_hop: 0 (optional)
- max_hop: 5 (optional)
- asset: USDT (optional)
- sort_by: timestamp|amount (default: timestamp)
- sort_order: asc|desc (default: desc)
- page: 1
- per_page: 50

Response (200 OK):
{
  "transactions": [
    {
      "transaction_id": "uuid",
      "transaction_hash": "0xDEF456...",
      "blockchain": "ethereum",
      "block_number": 18234567,
      "block_timestamp": "2026-09-20T14:23:11Z",
      "from_address": "0xABC123...",
      "to_address": "0xGHI789...",
      "asset_symbol": "USDT",
      "amount": "1200.00",
      "transaction_type": "token_transfer",
      "status": "confirmed",
      "discovered_at_hop": 1
    }
  ],
  "pagination": { ... }
}
```

**GET /cases/{case_id}/transactions/{transaction_id}**  
Detailed transaction information.

```json
Response (200 OK):
{
  "transaction_id": "uuid",
  "transaction_hash": "0xDEF456...",
  "blockchain": "ethereum",
  "block_number": 18234567,
  "block_timestamp": "2026-09-20T14:23:11Z",
  "from_address": "0xABC123...",
  "to_address": "0xGHI789...",
  "asset_symbol": "USDT",
  "amount": "1200.00",
  "token_contract_address": "0xdac17f958d2ee523a2206206994597c13d831ec7",
  "transaction_type": "token_transfer",
  "gas_fee": "0.0021",
  "gas_fee_asset": "ETH",
  "status": "confirmed",
  "confirmation_count": 15,
  "provider_source": "alchemy",
  "discovered_at_hop": 1,
  "from_wallet": {
    "wallet_id": "uuid",
    "label": "Initial Suspect Wallet"
  },
  "to_wallet": {
    "wallet_id": "uuid",
    "label": "Intermediary Wallet 1"
  }
}
```

---

### 4.4 Graph

**GET /cases/{case_id}/graph**  
Retrieve transaction graph data for visualization.

```json
Query Parameters:
- max_depth: 5 (optional, override default)
- format: json|cytoscape (optional, default: json)

Response (200 OK):
{
  "graph_id": "uuid",
  "case_id": "uuid",
  "root_wallet_address": "0xABC123...",
  "blockchain": "ethereum",
  "max_hop_depth": 5,
  "node_count": 47,
  "edge_count": 152,
  "generated_at": "2026-09-22T14:00:00Z",
  "nodes": [
    {
      "id": "0xABC123...",
      "type": "wallet",
      "label": "Initial Suspect Wallet",
      "hop": 0,
      "wallet_type": "suspect",
      "risk_score": 87,
      "vasp_entity": null
    },
    {
      "id": "0xGHI789...",
      "type": "wallet",
      "label": "Intermediary Wallet 1",
      "hop": 1,
      "wallet_type": "intermediary",
      "risk_score": 62,
      "vasp_entity": null
    }
  ],
  "edges": [
    {
      "id": "uuid",
      "source": "0xABC123...",
      "target": "0xGHI789...",
      "transaction_hash": "0xDEF456...",
      "amount": "1200.00",
      "asset": "USDT",
      "timestamp": "2026-09-20T14:23:11Z",
      "hop": 1
    }
  ]
}
```

**POST /cases/{case_id}/graph/expand**  
Request graph expansion (additional hops).

```json
Request:
{
  "additional_hops": 2,
  "branch_limit": 50,
  "dust_threshold": "10.00"
}

Response (202 Accepted):
{
  "job_id": "uuid",
  "status": "queued",
  "message": "Graph expansion job queued"
}
```

---

### 4.5 Patterns

**GET /cases/{case_id}/patterns**  
List detected patterns in case.

```json
Response (200 OK):
{
  "patterns": [
    {
      "pattern_id": "uuid",
      "pattern_type": "peel_chain",
      "description": "Detected peel chain pattern with 8 sequential small transfers",
      "confidence": 0.89,
      "wallet_id": "uuid",
      "wallet_address": "0xABC123...",
      "detected_at": "2026-09-22T14:03:00Z",
      "metrics": {
        "transfer_count": 8,
        "total_peeled_amount": "400.00",
        "remaining_amount": "4400.00"
      }
    }
  ]
}
```

---

### 4.6 Entity Intelligence

**GET /entities**  
Search entity registry.

```json
Query Parameters:
- entity_type: exchange|vasp|mixer (optional)
- search: binance (optional, name search)
- blockchain: ethereum (optional)
- page: 1
- per_page: 50

Response (200 OK):
{
  "entities": [
    {
      "entity_id": "uuid",
      "name": "Binance",
      "entity_type": "exchange",
      "verification_status": "verified",
      "address_count": 247,
      "first_seen": "2024-01-15T00:00:00Z"
    }
  ],
  "pagination": { ... }
}
```

**GET /entities/{entity_id}**  
Detailed entity information.

```json
Response (200 OK):
{
  "entity_id": "uuid",
  "name": "Binance",
  "entity_type": "exchange",
  "description": "Global cryptocurrency exchange",
  "verification_status": "verified",
  "confidence": 1.0,
  "source": "official_exchange_registry",
  "addresses": [
    {
      "address_id": "uuid",
      "blockchain": "ethereum",
      "address": "0x123ABC...",
      "address_type": "hot_wallet",
      "label": "Binance Hot Wallet 14",
      "verified": true
    }
  ],
  "first_seen": "2024-01-15T00:00:00Z",
  "last_verified": "2026-09-20T00:00:00Z"
}
```

---

### 4.7 Evidence

**POST /cases/{case_id}/evidence**  
Pin evidence (transaction, wallet, entity, pattern).

```json
Request:
{
  "evidence_type": "transaction",
  "reference_id": "uuid" (transaction_id, wallet_id, etc.),
  "investigator_note": "Key transaction showing rapid forwarding to mixer"
}

Response (201 Created):
{
  "evidence_id": "uuid",
  "evidence_type": "transaction",
  "pinned_at": "2026-09-22T15:00:00Z"
}
```

**GET /cases/{case_id}/evidence**  
List all pinned evidence for case.

```json
Response (200 OK):
{
  "evidence": [
    {
      "evidence_id": "uuid",
      "evidence_type": "transaction",
      "reference_id": "uuid",
      "reference_summary": {
        "transaction_hash": "0xDEF456...",
        "amount": "1200.00",
        "asset": "USDT"
      },
      "investigator_note": "Key transaction showing rapid forwarding to mixer",
      "pinned_at": "2026-09-22T15:00:00Z"
    }
  ]
}
```

---

### 4.8 Notes

**POST /cases/{case_id}/notes**  
Add investigator note to case.

```json
Request:
{
  "content": "Contacted victim for additional details. Confirmed transaction hash matches bank records."
}

Response (201 Created):
{
  "note_id": "uuid",
  "created_at": "2026-09-22T15:30:00Z"
}
```

**GET /cases/{case_id}/notes**  
List all notes for case.

```json
Response (200 OK):
{
  "notes": [
    {
      "note_id": "uuid",
      "content": "Contacted victim for additional details.",
      "created_at": "2026-09-22T15:30:00Z",
      "updated_at": "2026-09-22T15:30:00Z"
    }
  ]
}
```

---

### 4.9 Reports

**POST /cases/{case_id}/reports**  
Generate investigation report.

```json
Request:
{
  "report_type": "detailed",
  "format": "pdf"
}

Response (202 Accepted):
{
  "job_id": "uuid",
  "status": "queued",
  "message": "Report generation job queued"
}
```

**GET /cases/{case_id}/reports**  
List all reports for case.

```json
Response (200 OK):
{
  "reports": [
    {
      "report_id": "uuid",
      "report_type": "detailed",
      "format": "pdf",
      "generated_at": "2026-09-22T16:00:00Z",
      "file_url": "/api/v1/reports/uuid/download"
    }
  ]
}
```

**GET /reports/{report_id}/download**  
Download generated report file.

```
Response (200 OK):
Content-Type: application/pdf (or application/json)
Content-Disposition: attachment; filename="CASE-2026-001234_report.pdf"

[Binary file content]
```

---

### 4.10 AI Copilot (Phase 5)

**POST /cases/{case_id}/copilot/ask**  
Ask AI assistant a question about the case.

```json
Request:
{
  "question": "Why is the initial wallet flagged as high risk?"
}

Response (200 OK):
{
  "answer": "The initial wallet (0xABC123...) is flagged as high risk (score: 87/100) due to multiple factors: ...",
  "citations": [
    {
      "type": "risk_factor",
      "reference_id": "uuid",
      "summary": "Rapid onward transfer pattern"
    }
  ],
  "confidence": 0.95
}
```

---

## 5. Error Handling

### 5.1 Standard Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "additional_context"
    }
  }
}
```

### 5.2 HTTP Status Codes

- `200 OK` — Successful request
- `201 Created` — Resource created successfully
- `202 Accepted` — Request accepted (async job queued)
- `400 Bad Request` — Invalid request (validation error)
- `401 Unauthorized` — Authentication required or invalid token
- `403 Forbidden` — Insufficient permissions
- `404 Not Found` — Resource not found
- `409 Conflict` — Resource conflict (duplicate)
- `422 Unprocessable Entity` — Semantic validation error
- `429 Too Many Requests` — Rate limit exceeded
- `500 Internal Server Error` — Server error
- `503 Service Unavailable` — External service (blockchain provider) unavailable

### 5.3 Error Codes

**Authentication/Authorization:**
- `INVALID_CREDENTIALS`
- `TOKEN_EXPIRED`
- `INSUFFICIENT_PERMISSIONS`

**Validation:**
- `INVALID_ADDRESS`
- `INVALID_TRANSACTION_HASH`
- `INVALID_BLOCKCHAIN`
- `MISSING_REQUIRED_FIELD`
- `INVALID_FIELD_FORMAT`

**Resource:**
- `CASE_NOT_FOUND`
- `WALLET_NOT_FOUND`
- `TRANSACTION_NOT_FOUND`

**External Service:**
- `PROVIDER_TIMEOUT`
- `PROVIDER_RATE_LIMIT`
- `PROVIDER_UNAVAILABLE`
- `DATA_INCOMPLETE`
- `CHAIN_UNSUPPORTED`

**Business Logic:**
- `TRACE_IN_PROGRESS`
- `TRACE_FAILED`
- `REPORT_GENERATION_FAILED`

---

## 6. Pagination

### 6.1 Pagination Pattern

All list endpoints support pagination.

**Query Parameters:**
- `page` (integer, default: 1)
- `per_page` (integer, default: 20, max: 100)

**Response Structure:**
```json
{
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

---

## 7. Filtering & Sorting

### 7.1 Common Filters

- `blockchain` — Filter by blockchain (ethereum, tron)
- `status` — Filter by status (active, closed)
- `min_amount` / `max_amount` — Amount range
- `min_hop` / `max_hop` — Hop depth range
- `from_date` / `to_date` — Date range

### 7.2 Sorting

**Query Parameters:**
- `sort_by` — Field to sort by (e.g., timestamp, amount)
- `sort_order` — Sort direction (asc, desc)

---

## 8. Async Jobs

### 8.1 Job Status Tracking

Long-running operations (trace, graph expansion, report generation) return a job ID.

**GET /jobs/{job_id}**
```json
Response (200 OK):
{
  "job_id": "uuid",
  "job_type": "trace",
  "status": "processing",
  "progress": 65,
  "started_at": "2026-09-22T14:00:00Z",
  "estimated_completion": "2026-09-22T14:05:00Z"
}

Status values: queued, processing, completed, failed
```

---

## 9. Rate Limiting

### 9.1 Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1695394800
```

### 9.2 Rate Limit Response

```
HTTP 429 Too Many Requests

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Retry after 60 seconds.",
    "details": {
      "retry_after": 60
    }
  }
}
```

---

## 10. API Versioning Strategy

### 10.1 URL-Based Versioning

- Current: `/api/v1/...`
- Future: `/api/v2/...`

### 10.2 Breaking Changes

Breaking changes require new API version. Non-breaking changes (new optional fields, new endpoints) may be added to existing version.

---

## 11. Security Considerations

### 11.1 Input Validation

- All addresses validated against blockchain format rules
- Transaction hashes validated for length/format
- Amount values validated for positive decimal
- Enum values validated against allowed values

### 11.2 Output Sanitization

- HTML entities escaped in report generation
- SQL injection prevention (ORM parameterized queries)
- No raw provider data exposed to frontend

### 11.3 Authentication

- JWT tokens with expiration
- Secure password hashing (bcrypt)
- HTTPS only in production

---

## 12. OpenAPI Specification

In Phase 1 implementation, FastAPI will auto-generate OpenAPI (Swagger) documentation at:

```
GET /docs (Swagger UI)
GET /redoc (ReDoc UI)
GET /openapi.json (OpenAPI spec)
```

---

## 13. WebSocket Endpoints (Future)

For real-time updates (job progress, new transactions discovered):

```
WS /ws/cases/{case_id}
```

Message format:
```json
{
  "event": "trace_progress",
  "data": {
    "job_id": "uuid",
    "progress": 75,
    "new_wallets_count": 12
  }
}
```

---

**Document Status:** Initial API contract for Phase 0  
**Approval Required:** MASTER / CTO  
**Dependencies:** ARCHITECTURE.md, DOMAIN_MODEL.md  
**Implementation:** Backend Engineer (Phase 1)
