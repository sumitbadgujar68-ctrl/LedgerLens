# Phase 7 Security Audit — LedgerLens

**Task:** TASK-P7-001 (Phase 7 Step 1)  
**Auditor:** Security Engineer (activated 2026-09-25)  
**Date:** 2026-09-25  
**Audited revision:** `ccb71ab` — "Phase 6 COMPLETE: investigation reporting and export pipeline" (branch `master`, working tree clean)  
**Authoritative requirements:** `docs/SECURITY_MODEL.md`, `docs/ARCHITECTURE.md` §8.4/§8.5/§9.1, `docs/API_CONTRACT.md` §3/§5/§9/§11, `docs/DATA_MODEL.md` §12, `docs/DEVELOPMENT_STANDARDS.md` §6/§7/§10, `docs/MASTER_BOOTSTRAP.md` §18  
**Status:** AUDIT COMPLETE (2026-09-25) — TASK-P7-002 remediation applied for SEC-01…SEC-06 (record in §11); MEDIUM/LOW findings still open
**Approval required:** MASTER / CTO before remediation begins

---

## 1. Scope and Method

**In scope:** backend application (`backend/app/**`), frontend (`frontend/src/**`), schema and migrations (`migrations/**`), dependency manifests (`backend/requirements.txt`, `frontend/package.json`, `frontend/package-lock.json`), configuration (`.env.example`, `app/config.py`, CORS/middleware), logging, and the documentation that specifies security controls.

**Method:** static/code review of every registered route, service module, migration and config file; repository secret scan; framework-route enumeration via the FastAPI application object; control-by-control assessment against `SECURITY_MODEL.md` §4-§13 and the §14 review gates; OWASP Top 10 (2021) mapping.

**Out of scope for this task (deferred to TASK-P7-003 / TASK-P7-004):** dynamic penetration testing, load/performance testing, live-database control verification.

**Constraint honored:** the audit itself changed no product code. Only this document was written.

---

## 2. Executed Route Inventory

Enumerated directly from the running application object (`app.routes`) — 22 routes:

| Category | Count | Routes |
|---|---|---|
| API endpoints (implemented) | **16** | cases (4), traces (3), risk (3), copilot (3), reports (3) |
| Framework documentation endpoints | **4** | `GET /openapi.json`, `GET /docs`, `GET /docs/oauth2-redirect`, `GET /redoc` |
| Service metadata | **2** | `GET /`, `GET /health` |

**All 16 API endpoints are anonymously reachable** — no authentication dependency exists anywhere in `backend/app/**`.

---

## 3. Executive Summary

| Severity | Count | IDs |
|---|---|---|
| CRITICAL | 2 | SEC-01, SEC-02 |
| HIGH | 4 | SEC-03, SEC-04, SEC-05, SEC-06 |
| MEDIUM | 8 | SEC-07 … SEC-14 |
| LOW | 4 | SEC-15 … SEC-18 |
| **Total findings** | **18** | |
| Verified controls (PASS) | 11 | V-01 … V-11 |
| Not-verifiable checks (external dependency) | 5 | NV-01 … NV-05 |
| Documentation/contract discrepancies | 5 | DOC-01 … DOC-05 |

**Top risk:** the application implements strong *content-level* defenses (XSS escaping, path-traversal guards, parameterized queries, provider key redaction) but has **no authentication or authorization layer at all**, while holding sensitive fraud-investigation data. Content protections do not compensate for an open access boundary.

---

## 4. Findings Register

Severity: CRITICAL = immediate data compromise; HIGH = significant compromise or direct spec violation; MEDIUM = meaningful weakness / defense-in-depth loss; LOW = hardening.

| ID | Sev | OWASP Top 10 (2021) | Requirement violated | Location |
|---|---|---|---|---|
| SEC-01 | CRITICAL | A01 Broken Access Control | `SECURITY_MODEL.md:254-261` (§7.1), `ARCHITECTURE.md:803`, `API_CONTRACT.md:58-128` | `backend/app/main.py:19-23` (all routers), no auth module in `backend/app/**` |
| SEC-02 | CRITICAL | A01 Broken Access Control | `SECURITY_MODEL.md:263-270` (§7.2), `SECURITY_MODEL.md:410-418` (§10.2) | `backend/app/api/v1/reports.py:174-198`; `cases.py` get/put/list |
| SEC-03 | HIGH | A01 / A04 Insecure Design | `SECURITY_MODEL.md:410-418`, `DATA_MODEL.md` `reports.generated_by` FK | `backend/app/api/v1/reports.py:18, 80, 88, 90` |
| SEC-04 | HIGH | A05 Security Misconfiguration | `SECURITY_MODEL.md:299-306` (§7.5) | `backend/app/main.py:13-16` |
| SEC-05 | HIGH | A05 / A09 Logging & Monitoring Failures | `SECURITY_MODEL.md:481-493` (§12.2), `DEVELOPMENT_STANDARDS.md` §7.1 | `backend/app/db/database.py:7` (`echo=True`) |
| SEC-06 | HIGH | A05 Security Misconfiguration | `SECURITY_MODEL.md:256` (auth on all endpoints except `/health`) | `backend/app/main.py:7-9` (defaults enabled) → `/docs`, `/redoc`, `/openapi.json`, `/docs/oauth2-redirect` |
| SEC-07 | MEDIUM | A05 | `SECURITY_MODEL.md:308-316` (§7.6) | `backend/app/api/v1/copilot.py:34, 39, 44, 49`; `reports.py:102, 115, 128` |
| SEC-08 | MEDIUM | A04 Insecure Design | `SECURITY_MODEL.md:289-297` (§7.4), `API_CONTRACT.md:875-900` | `backend/app/main.py:11-17` (only CORS middleware) |
| SEC-09 | MEDIUM | A05 | `SECURITY_MODEL.md:308-316` (§7.6) | `backend/app/api/v1/traces.py:44-47, 106` |
| SEC-10 | MEDIUM | A09 Logging & Monitoring Failures | `SECURITY_MODEL.md:456-503` (§12), `ARCHITECTURE.md:776-796, 832` | no logging configuration in `backend/app/**` (0 hits for `basicConfig`/`dictConfig`) |
| SEC-11 | MEDIUM | A05 Security Misconfiguration | `ARCHITECTURE.md:800-817`, `DEVELOPMENT_STANDARDS.md` §7 | `backend/app/main.py:11-17` (no security headers middleware) |
| SEC-12 | MEDIUM | A06 Vulnerable and Outdated Components | `SECURITY_MODEL.md:506-527` (§13.1/§13.2) | `backend/requirements.txt`, `frontend/package.json` — scan **not executed** |
| SEC-13 | MEDIUM | A06 / A02 | `SECURITY_MODEL.md:24-27` (least privilege) | `backend/requirements.txt` declares `python-jose[cryptography]==3.3.0`, `passlib[bcrypt]==1.7.4` — **zero imports in `backend/app/**`** |
| SEC-14 | MEDIUM | A02 Cryptographic Failures | `SECURITY_MODEL.md:139-155` (§4.4) | `backend/app/config.py:5` (`secret_key: str`, no strength validation); `backend/.env.example:2` |
| SEC-15 | LOW | A05 | `ARCHITECTURE.md:816` (don't expose internals) | `backend/app/main.py:27-32` — also reports stale `"phase": "Phase 5 - AI Copilot"` |
| SEC-16 | LOW | A05 | `SECURITY_MODEL.md:308-316` | `backend/app/api/v1/reports.py:199-201` (DB value interpolated into `Content-Disposition`) |
| SEC-17 | LOW | A02 / §12.2 | `SECURITY_MODEL.md:322-338, 481-493` | `backend/app/services/blockchain/adapter.py:161-166` vs `providers/alchemy.py:71, 79-82` |
| SEC-18 | LOW | A01 (contextual) | `SECURITY_MODEL.md` §7 (no cookie sessions today) | no CSRF defenses anywhere — relevant only together with SEC-01 |

### 3.1 CRITICAL — detail

**SEC-01 — No authentication on any API endpoint.**
`backend/app/main.py:19-23` registers `cases`, `traces`, `risk`, `copilot`, `reports`. A repository-wide search of `backend/app/**` for `HTTPBearer`, `OAuth2`, `get_current_user`, `jwt`, `jose`, `passlib`, `bcrypt` returns **no imports**. Requirements declare `python-jose` and `passlib[bcrypt]` (`backend/requirements.txt:8-9`) but they are unused (SEC-13). `SECURITY_MODEL.md:256` requires authentication on all endpoints except `/health`; `ARCHITECTURE.md:803` requires the same; `API_CONTRACT.md:58-128` specifies JWT bearer flow and `/auth/login`, `/auth/logout`, `/auth/me` — **none of which exist as routes**. `backend/app/db/models.py:14` defines `password_hash` (NOT NULL), i.e. the data model presumes credentials that no code path ever verifies.
*Impact:* every case, trace, risk score, evidence item and report is readable and writable by any unauthenticated client.
*Remediation:* implement JWT bearer authentication + token-validation middleware per `API_CONTRACT.md:3.1-3.2`; exempt only `/` and `/health`; add 401 semantics tests.
*Owner:* Backend Engineer (implementation) · Security Engineer (verification) · MASTER (approval)

**SEC-02 — No authorization / resource scoping (IDOR).**
`reports.py:174-198` resolves a report solely by `report_id` (UUID) with no caller identity and no case-ownership check before returning its content; `GET/PUT /cases/{case_id}` and `GET /cases` have no owner filter. `SECURITY_MODEL.md:263-270` requires case ownership validation and 403 on unauthorized access; `SECURITY_MODEL.md:416` requires report download to verify case ownership.
*Impact:* even after SEC-01 is fixed, any authenticated user could read/modify any case and download any report.
*Dependency:* requires SEC-01 (there is no principal to check today).
*Owner:* Backend Engineer · Security Engineer (verification)

### 3.2 HIGH — detail

**SEC-03 — Report chain of custody is attributed to a hard-coded identity.**
`reports.py:18` imports `MOCK_INVESTIGATOR_ID` from `cases.py`; it is used as `initiated_by` (`:80`), `generated_by` (`:88`) and the `save_report` actor (`:90`). In a forensics tool this falsifies provenance: every report claims the same synthetic investigator. Violates `SECURITY_MODEL.md:410-418` (report access control) and the `reports.generated_by → investigators` foreign key semantics in `DATA_MODEL.md`.
*Remediation:* derive the investigator from the authenticated principal (blocked by SEC-01); until then this must be documented as a blocking limitation, not a passing control.
*Owner:* Backend Engineer

**SEC-04 — Wildcard CORS with credentials.**
`main.py:13-16` sets `allow_origins=["*"]`, `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`. `SECURITY_MODEL.md:304-306` forbids wildcard CORS in production and allows only the frontend origin plus `localhost:3000` in development. (Wildcard origins combined with credentials are also rejected by conforming browsers — the configuration is both insecure and spec-invalid.)
*Remediation:* origin allow-list driven by an environment variable (`CORS_ALLOWED_ORIGINS`), no credentials until authentication exists.
*Owner:* Backend Engineer

**SEC-05 — SQL statements and bind parameters logged unconditionally.**
`backend/app/db/database.py:7`: `create_async_engine(DATABASE_URL, echo=True, future=True)`. SQLAlchemy `echo=True` emits every SQL statement **and its bound parameter values** to the logger in every environment. Case narratives, wallet addresses, investigator IDs and report content would all be written to stdout. Violates `SECURITY_MODEL.md:481-493` (never log sensitive data) and the logging standard in `DEVELOPMENT_STANDARDS.md` §7.1.
*Remediation:* default `echo=False`, gate on an explicit `SQL_ECHO` environment flag for local debugging only.
*Owner:* Backend Engineer

**SEC-06 — Interactive API schema and "Try it out" console exposed without authentication.**
The FastAPI app is constructed without `docs_url` / `redoc_url` / `openapi_url` overrides (`main.py:7-9`), so `/docs`, `/docs/oauth2-redirect`, `/redoc` and `/openapi.json` are served by default — confirmed by route enumeration (§2). Together with SEC-01 this hands an unauthenticated attacker a complete, callable attack-surface map.
*Remediation:* disable docs routes outside development (`docs_url=None` in production config) or place them behind authentication.
*Owner:* Backend Engineer

### 3.3 MEDIUM and LOW — summary

| ID | Finding | Evidence | Remediation direction |
|---|---|---|---|
| SEC-07 | Internal exception text returned to clients | `copilot.py:34, 39, 44, 49` (`str(e)`); `reports.py:102, 115, 128` (`f"Report generation failed: {e}"`) | Generic client message; detail already logged server-side (`reports.py:107, 120`) |
| SEC-08 | No API rate limiting; documented 429 behaviour never emitted | `main.py:11-17`; `API_CONTRACT.md:875-900`; `SECURITY_MODEL.md:289-297` | Per-IP/per-user limiter middleware (100/min per IP per spec) |
| SEC-09 | Configuration/provider internals disclosed in responses | `traces.py:44-47` returns `"ALCHEMY_API_KEY is not configured"`; `traces.py:106` returns persisted provider `errors` | Generic `PROVIDER_UNAVAILABLE` to client, detail logged |
| SEC-10 | No logging configuration, no security-event logging, no monitoring | 0 hits for `basicConfig`/`dictConfig`; 10 bare `getLogger` call sites; `SECURITY_MODEL.md:456-503` | Structured logging config + security event schema + alerting hooks |
| SEC-11 | No security response headers | only `CORSMiddleware` registered | HSTS, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, CSP |
| SEC-12 | Dependency vulnerability scan never run | `pip-audit`/`bandit` not installed; `npm audit` not executed (needs registry) | Run `pip-audit` + `npm audit` (NV-01), remediate advisories |
| SEC-13 | Unused auth dependencies declared | `requirements.txt:8-9` vs 0 imports in `backend/app/**` | Remove, or use them by implementing SEC-01 |
| SEC-14 | `SECRET_KEY` accepted with no strength/rotation policy | `config.py:5`; `.env.example:2` placeholder | Validate minimum length/entropy at startup; document rotation (`SECURITY_MODEL.md:139-155`) |
| SEC-15 | Service metadata disclosed; stale phase string | `main.py:27-32` (`"phase": "Phase 5 - AI Copilot"`) | Correct the status string; gate detail behind debug config |
| SEC-16 | DB-derived value interpolated into a response header | `reports.py:199-201` (`case_number` → `Content-Disposition`) | Sanitize CR/LF and quotes before header use |
| SEC-17 | Unexpected provider exceptions may bypass key redaction | `alchemy.py:71` embeds the API key in the URL path; `adapter.py:161-166` appends `f"unexpected_error: {exc}"` and logs a full traceback **without** `_sanitize` | Route unexpected errors through the same redaction (`alchemy.py:79-82`) |
| SEC-18 | No CSRF defenses | no token/`SameSite` handling anywhere | Implement together with SEC-01 if cookie-based sessions are ever used (JWT header auth does not require it) |

---

## 5. Verified Controls (PASSED)

| ID | Control | Requirement | Evidence |
|---|---|---|---|
| V-01 | No secrets committed | `SECURITY_MODEL.md:139-155` | `git ls-files` scan for `AKIA…`, `sk-…`, `BEGIN … PRIVATE KEY` → **0 hits**; `backend/.env` is ignored and untracked (`git status --ignored`); `backend/.env.example` uses placeholders only |
| V-02 | Secrets read from environment only | `ARCHITECTURE.md:809-811` | `backend/app/config.py` (`pydantic-settings`, `env_file=".env"`); no key literals in tracked source |
| V-03 | Provider API key redaction in error messages | `SECURITY_MODEL.md:322-338, 490-493` | `providers/alchemy.py:79-82` `_sanitize()` replaces the key with `***`, applied at `:138, :143, :151, :158, :173` |
| V-04 | Report HTML export XSS defense | `SECURITY_MODEL.md:400-408` (§10.1) | `reporting/render.py:23` (`html.escape`), `:111-113` `escape_value(..., quote=True)` used at `:219, :228, :254-255, :272, :275, :281, :292, :309, :317, :328`; strict CSP at `:213-215` (`script-src 'none'; object-src 'none'`); no inline script anywhere in the template |
| V-05 | Artifact path-traversal guard | `SECURITY_MODEL.md:286` | `reporting/artifacts.py:88-91` `resolved.is_relative_to(root)` rejects paths outside the artifact root; `:21, :40-43` sanitize filename charset to `[A-Za-z0-9._-]` |
| V-06 | Parameterized queries / SQL injection defense | `SECURITY_MODEL.md:434-442` (§11.2) | All persistence uses SQLAlchemy `select()`/`execute(stmt)` (`risk.py:103…247`, `traces.py:126, 170`, `case_service.py:32, 43, 53`, `factors.py:270`, `address_registry.py:25, 34`); no `sqlalchemy.text()` or string-built SQL in `backend/app/**`; raw SQL exists only in `migrations/*.sql` |
| V-07 | Input validation at the API boundary — partial | `SECURITY_MODEL.md:272-281` | Pydantic request models on all 16 routes; Ethereum address regex `^0x[0-9a-fA-F]{40}$` at `blockchain/adapter.py:24` with `validate_address` at `:37, :54, :66` and request-level validation `traces.py:39`. **Gap:** no transaction-hash format validation (see NV-06 / DOC-04) |
| V-08 | Provider rate-limit *handling* (distinct from API rate limiting) | `SECURITY_MODEL.md:350-360` | `blockchain/errors.py:10, 37` `RATE_LIMITED`; `adapter.py:147, 223` maps HTTP 429 → `RATE_LIMITED`; `tracing/service.py:119` surfaces it explicitly. This does **not** satisfy SEC-08 (API-side limiting) |
| V-09 | Frontend has no dangerous DOM/storage sinks | `SECURITY_MODEL.md:364-396` (§9) | Scan of `frontend/src/**` for `innerHTML`, `dangerouslySetInnerHTML`, `eval(`, `localStorage`, `sessionStorage`, `document.cookie` → **0 hits**; React escapes by default |
| V-10 | Frontend exposes no secrets to the bundle | `SECURITY_MODEL.md:387-396` | No `import.meta.env` usage in `frontend/src/**`; no `VITE_*` secrets in tracked files |
| V-11 | Report download never fabricates output | `SECURITY_MODEL.md` fail-secure (`:27`) | `reports.py:222-233` returns 404 `REPORT_NOT_AVAILABLE` for HTML/PDF without a stored artifact rather than regenerating content |

---

## 6. Checks That Could NOT Be Verified (external dependency — do not read as "pass")

| ID | Check | Why blocked | Classification |
|---|---|---|---|
| NV-01 | Dependency vulnerability scan (`pip-audit`, `bandit`, `npm audit`) | `pip-audit`/`bandit` not installed; `npm audit` requires registry access. Pinned backend versions are 2023-era (`fastapi==0.104.1`, `uvicorn==0.24.0`, `pydantic==2.5.0`, `sqlalchemy==2.0.23`, `asyncpg==0.29.0`, `python-jose==3.3.0`, `passlib==1.7.4`, `openai==3.19.2`, `httpx==0.25.2`) | **NOT VERIFIED** — needs tooling approval + network |
| NV-02 | Dynamic/penetration testing (OWASP ZAP per `SECURITY_MODEL.md:650`) | requires a running service with a reachable target and the ZAP tool; not executed in this task | **NOT VERIFIED** |
| NV-03 | Database-level controls: RLS, least-privilege DB role, TLS to DB, backups | no live database (`postgresql://…localhost:5432` → connection refused); grep of `migrations/*.sql` shows **no `ENABLE ROW LEVEL SECURITY` / `POLICY` statements** | **NOT VERIFIED** (`SECURITY_MODEL.md:541` "Database RLS configured" cannot be checked) |
| NV-04 | Production transport security (HTTPS/HSTS), deployment configuration | no deployment target or server configuration exists in the repository | **NOT VERIFIED** — belongs to TASK-P7-005 |
| NV-05 | Authentication token expiry, refresh, revocation, failed-login lockout | authentication is not implemented (SEC-01); nothing to test | **NOT VERIFIED** |

---

## 7. `SECURITY_MODEL.md` §14 Review-Gate Assessment

### §14.1 Phase 0 (Foundation) — all originally checked
- [x] Secrets management strategy defined — **VERIFIED** (documented §4.4)
- [x] Authentication approach documented — **VERIFIED** (`API_CONTRACT.md:62-73`, `SECURITY_MODEL.md:157-175`)
- [x] API security requirements specified — **VERIFIED** (`SECURITY_MODEL.md:252-316`)

### §14.2 Phase 1 (Case Foundation)
- [ ] Authentication implemented — **FAIL (SEC-01)**
- [ ] Authorization implemented — **FAIL (SEC-02)**
- [x] Input validation implemented — **PARTIAL/PASS (V-07)**; transaction-hash validation missing (DOC-04)
- [ ] Database RLS configured — **NOT VERIFIED (NV-03)**

### §14.3 Phase 2 (Blockchain Foundation)
- [x] API key protection verified — **PARTIAL (V-03 + SEC-17)**
- [x] Provider request sanitization implemented — **PASS (V-03)**
- [x] Rate limit handling implemented — **PASS for provider-side (V-08)**; API-side absent (SEC-08)

### §14.4 Phase 3 (Investigation UI)
- [x] XSS prevention verified — **PASS (V-09)**, plus report escaping (V-04)
- [ ] Token storage implemented securely — **NOT VERIFIED (NV-05)** — no auth, no token store
- [ ] CORS policy configured — **FAIL (SEC-04)**

### §14.5 Phase 6 (Reporting)
- [x] Report sanitization implemented — **PASS (V-04, V-11)**
- [ ] Report access control verified — **FAIL (SEC-02, SEC-03)**

### §14.6 Phase 7 (Hardening)
- [x] Security audit conducted — **COMPLETE (this document)**
- [ ] Penetration testing (if feasible) — **NOT RUN (NV-02)**
- [ ] Vulnerability remediation — **PENDING (TASK-P7-002)**
- [x] Security documentation reviewed — **COMPLETE (§10 discrepancies below)**

---

## 8. Security Test Requirements (for TASK-P7-002 / TASK-P7-003)

Per `SECURITY_MODEL.md:625-642` (§17.1), the following tests must exist before Phase 7 can pass Quality criteria:

**Unit tests**
1. Authentication logic (token issue/validate/expiry) — blocked until SEC-01 lands
2. Authorization checks — case ownership, report access, 403 semantics (SEC-02)
3. Input validation — malformed addresses, malformed transaction hashes, oversized payloads
4. Sanitization functions — HTML escaping, header-value sanitizing (SEC-16), key redaction (SEC-17)

**Integration tests**
5. API authentication/authorization on all 16 routes (401/403)
6. Rate limiting → 429 with documented headers (SEC-08, `API_CONTRACT.md:875-900`)
7. Token expiry handling

**Security tests**
8. SQL injection attempts (against every parameterized filter)
9. XSS payload attempts (report HTML export, case notes, API responses)
10. Authentication bypass attempts (missing/garbage/expired token)
11. CSRF attempts (only if cookie sessions are introduced)

Ownership: test authorship belongs to the owning engineer + QA Engineer; Security Engineer verifies coverage.

---

## 9. Documentation / Contract Discrepancies Found (route to TASK-P7-006)

| ID | Discrepancy | Evidence |
|---|---|---|
| DOC-01 | `API_CONTRACT.md` documents **15 endpoints that do not exist**: `/auth/login`, `/auth/logout`, `/auth/me`, `GET /cases/{id}/wallets` (+`/{wallet_id}`), `GET /cases/{id}/transactions` (+`/{id}`), `GET /cases/{id}/graph`, `POST /cases/{id}/graph/expand`, `GET /cases/{id}/patterns`, `GET /entities` (+`/{id}`), `POST/GET /cases/{id}/evidence`, `POST/GET /cases/{id}/notes`, `GET /jobs/{job_id}` | `API_CONTRACT.md:77-648, 858` vs implemented route inventory (§2) |
| DOC-02 | **8 implemented endpoints are undocumented**: 3 trace routes, 3 risk routes, `POST /copilot/summarize`, `POST /copilot/explain_risk` | route inventory (§2) vs `API_CONTRACT.md` endpoint list |
| DOC-03 | `ARCHITECTURE.md:803` ("Authentication required for all endpoints"), `:805` (rate limiting), `:832` (audit logging), `SECURITY_MODEL.md:679-681` ("Security Status") describe controls that do not exist / are stale | see SEC-01, SEC-08, SEC-10 |
| DOC-04 | `SECURITY_MODEL.md:280` requires transaction-hash format validation; no such validation exists in `backend/app/**` | 0 regex/match hits for 64-hex hash validation |
| DOC-05 | Risk explanation route is registered as `/api/v1/cases/risk/{risk_id}/explanation` — no `case_id` segment, and it is not in the contract | route inventory (§2); `risk.py:28-44` |

---

## 10. Remediation Plan (maps to TASK-P7-002 — APPLIED 2026-09-25, see §11)

| Priority | Findings | Suggested task grouping | Prerequisite |
|---|---|---|---|
| P0 | SEC-01, SEC-02, SEC-03 | **Authentication + authorization layer** (JWT per `API_CONTRACT.md` §3, case ownership checks, authenticated investigator identity replacing `MOCK_INVESTIGATOR_ID`) | MASTER approves adding the auth surface (it is already specified, not a new feature) |
| P0 | SEC-04, SEC-06 | **Configuration hardening** (CORS allow-list, docs routes disabled outside dev) | none |
| P0 | SEC-05 | **Logging configuration** (`echo` off by default) | none |
| P1 | SEC-07, SEC-09, SEC-16, SEC-17 | **Error-handling and output sanitization** | none |
| P1 | SEC-08 | **API rate limiting** | none |
| P1 | SEC-10, SEC-11 | **Security event logging + response headers** | TASK-P7-005 (deployment/monitoring) for the alerting half |
| P1 | SEC-12, SEC-13 | **Dependency hygiene** — run `pip-audit`/`npm audit`, remove unused auth libs or implement auth | NV-01 tooling approval |
| P2 | SEC-14, SEC-15, SEC-18 | **Secrets policy, metadata trimming, CSRF posture** | none |
| P2 | DOC-01 … DOC-05 | **Documentation reconciliation** | TASK-P7-006 |

**Constraints on remediation:** no architecture, API-contract or schema redesign beyond controls already specified in `SECURITY_MODEL.md` / `API_CONTRACT.md`; every change lands through the owning agent per `AGENTS.md` File Ownership Rules; the existing baselines (backend 268/268, frontend 9/9) must stay green.

---

## 11. Remediation Record — TASK-P7-002 (applied 2026-09-25)

**Approved scope (MASTER / CTO):** SEC-01 and SEC-02 first, then the remaining CRITICAL/HIGH set; no performance, regression, deployment or unrelated Phase 7 work; existing Phase 1-6 functionality and tests preserved; only changes required by the documented findings; stop after verification.

**No dependency, migration, contract or schema change was introduced.** JWT comes from `python-jose` and hashing from `bcrypt`, both already declared in `backend/requirements.txt` (this also resolves SEC-13's "unused auth dependencies").

| Finding | Change | Evidence |
|---|---|---|
| SEC-01 | JWT bearer authentication on every data router; `require_auth` applied at router level so no endpoint can be added unprotected by accident; `/api/v1/auth/login`, `/logout`, `/me` implemented per `API_CONTRACT.md` §3.2; only `/` and `/health` stay public | `backend/app/main.py:25-33`, `backend/app/services/auth/deps.py:41-69`, `backend/app/api/v1/auth.py:37-122`, `backend/app/services/auth/security.py`, `backend/app/services/auth/service.py` |
| SEC-02 | `require_case_ownership` (403 `CASE_ACCESS_DENIED`) enforced on cases (get/update), all 3 trace routes, all 3 risk routes, all 3 copilot routes, and reports (create/list/download); `list`/`create` are scoped to the caller | `backend/app/services/auth/deps.py:94-99`, `backend/app/api/v1/cases.py:47,70`, `traces.py:199,240,265`, `risk.py:116,194,215`, `copilot.py:60-68,94,127,161`, `reports.py:86,158,197` |
| SEC-03 | Report chain of custody now records the authenticated investigator (`create_job`, `generated_by`, `save_report`); `MOCK_INVESTIGATOR_ID` no longer used by any endpoint | `backend/app/api/v1/reports.py:83,94,96`, `backend/app/api/v1/cases.py:35,60` |
| SEC-04 | CORS restricted to `CORS_ALLOWED_ORIGINS` (default `http://localhost:3000,http://127.0.0.1:3000`), methods/headers allow-listed, no wildcard | `backend/app/main.py:17-23`, `backend/app/config.py` (`cors_allowed_origins`, `cors_origins`) |
| SEC-05 | SQLAlchemy statement logging off by default (`SQL_ECHO=false`), opt-in via environment | `backend/app/db/database.py:7`, `backend/app/config.py` (`sql_echo`), `backend/.env.example` |
| SEC-06 | `/docs`, `/redoc`, `/openapi.json` disabled unless `ENABLE_DOCS=true` | `backend/app/main.py:12-14`, `backend/.env.example` |

**Frontend (required so the application still functions once SEC-01 lands):** `Authorization: Bearer` header attached centrally in `frontend/src/services/api.ts`; 401 clears the session and returns the UI to sign-in; `LoginPage` gate in `frontend/src/App.tsx`; sign-out control in `frontend/src/components/layout/TopBar.tsx`. Token storage uses `localStorage`, the option explicitly allowed by `SECURITY_MODEL.md` §9.2 ("secure localStorage with XSS protections"); `API_CONTRACT.md` §3.1 mandates the Authorization header, which rules out the HttpOnly-cookie option.

**Operational bootstrap:** `backend/scripts/create_investigator.py` creates/resets an investigator (password from `INVESTIGATOR_PASSWORD` or interactive prompt — never a CLI argument), because no credential store existed.

**Verification (all executed 2026-09-25):**

| Check | Result |
|---|---|
| Backend suite `python -m pytest -q` | **287/287 passed** (268 pre-existing + 19 new) |
| New security tests `backend/tests/test_security_auth.py` | 19 passed: missing/malformed/expired token → 401; valid token → 200; `/health`+`/` public; login success/wrong password/unknown user; `/auth/me`; password + token unit checks; foreign case → 403, owned case → 200; report download → 403; copilot → 403; `/docs`+`/redoc`+`/openapi.json` → 404; CORS allowed vs denied origin |
| Frontend `npx vitest run` | 9/9 passed (unchanged) |
| Frontend `npm run lint` (oxlint) | exit 0 |
| Frontend `npm run build` (`tsc -b && vite build`) | exit 0 |
| Route inventory | 19 API routes (16 protected + 3 auth), `/` and `/health` public, docs routes absent, CORS allow-list confirmed |

**Pre-existing test-suite accommodation:** `backend/tests/conftest.py` (new) overrides only the principal dependency so the 268 existing tests keep exercising their original route logic as the fixture owner; no existing assertion was changed. One fixture in `backend/tests/test_copilot.py` (`_override_get_db_stub`) now returns an owned case so the copilot API tests exercise their documented 503/502/200 paths against the new ownership check — the three `*_nonexistent_case_returns_404` tests still assert `CASE_NOT_FOUND`.

**Not remediated (unchanged from §6/§10):** all MEDIUM findings SEC-07…SEC-14, all LOW findings SEC-15…SEC-18, documentation discrepancies DOC-01…DOC-05 (→ TASK-P7-006), and dependency-scan / dynamic / DB-level checks NV-01…NV-05.

**Limitations introduced or newly observed:**
1. Real-database login/authorization could not be executed (no DB connectivity); login, `/auth/me` and ownership are verified against request stubs only.
2. Logout is stateless: JWTs are not revoked server-side (no denylist store available) — token expiry remains the backstop.
3. Account lockout after 5 failed attempts (`SECURITY_MODEL.md` §5.1) is not implemented — it was not in this register and requires persistence for attempt counters.
4. `GET /` remains public and still reports the stale Phase 5 string (SEC-15, deferred).
5. **Pre-existing defect found during remediation, not fixed (out of approved scope):** `backend/app/services/ai/engine.py:322` — `get_copilot_engine(db)` lacks `Depends(get_db)`, so FastAPI reads `db` as a required query parameter and un-overridden copilot API calls return 422. Functional, not security. Requires a separate MASTER-approved fix.

---

## 12. Audit Sign-off

- Findings are evidence-based: every entry cites `file:line` or a verified command result.
- No control is reported as passing unless it was executed/inspected in this session.
- Checks that could not run are listed in §6 as **NOT VERIFIED** with their external dependency.
- The audit itself modified no product code; the §11 remediation was applied only after explicit MASTER / CTO approval.

**Prepared by:** Security Engineer (Phase 7, activated 2026-09-25)  
**Approved by:** ✅ MASTER / CTO — 2026-09-25 (audit checkpoint committed as `7e6d02c`; TASK-P7-002 authorized with SEC-01/SEC-02 priority, CRITICAL+HIGH scope)  
**Next task:** TASK-P7-003 (regression) / TASK-P7-004…007 — **not started**, awaiting MASTER instruction; MEDIUM/LOW findings and DOC-01…DOC-05 remain open
