# LedgerLens Security Model

**Last Updated:** 2026-09-22  
**Phase:** PHASE 0 — FOUNDATION  
**Status:** Initial Security Specification

---

## 1. Overview

LedgerLens handles sensitive investigative data, cryptocurrency intelligence, and integrates with external blockchain APIs. This document defines security principles, threat model, and security requirements across all system components.

**Security Priority:** HIGH  
**Domain:** Financial crime investigation  
**Data Sensitivity:** Case data, investigator identities, blockchain intelligence

---

## 2. Security Principles

### 2.1 Defense in Depth
Multiple layers of security controls at frontend, API, service, and data layers.

### 2.2 Least Privilege
Services, users, and components have only necessary permissions.

### 2.3 Fail Secure
Failures default to denying access, not granting it.

### 2.4 No Security Through Obscurity
Security relies on strong authentication, encryption, and access controls, not hidden implementation details.

### 2.5 Privacy by Design
Minimize PII collection. Separate demo data from production data.

### 2.6 Auditability
Security-relevant actions are logged with timestamps and actor identity.

---

## 3. Threat Model

### 3.1 Threat Actors

**External Attackers:**
- Criminals seeking to identify investigative activity
- Competitors seeking intelligence data
- General malicious actors

**Insider Threats:**
- Unauthorized investigator access to cases
- Data exfiltration
- Misuse of blockchain intelligence

**Infrastructure Threats:**
- Cloud provider compromise
- Third-party service compromise (Alchemy, Supabase)
- Dependency vulnerabilities

### 3.2 Assets to Protect

**Critical:**
- Case investigation data
- Investigator identities
- API keys (Alchemy, Etherscan, TronGrid)
- Database credentials
- Authentication tokens

**Sensitive:**
- Blockchain transaction data
- Entity attribution intelligence
- VASP identification data
- Evidence notes
- Investigation reports

**Public:**
- Aggregated blockchain statistics (if any)
- Public documentation

### 3.3 Attack Vectors

**Application Layer:**
- SQL injection
- API abuse/enumeration
- Authentication bypass
- Authorization bypass
- XSS in reports

**Infrastructure Layer:**
- Credential theft
- Man-in-the-middle
- DDoS

**Social Engineering:**
- Phishing for investigator credentials
- Impersonation

---

## 4. Credential Management

### 4.1 Blockchain API Keys

**Requirement:** All blockchain provider API keys (Alchemy, Etherscan, TronGrid) MUST remain server-side only.

**Enforcement:**
- API keys stored in environment variables
- Never included in frontend code
- Never committed to repository
- Never exposed in API responses
- Never logged in plain text

**Access Control:**
- Backend services only
- Rotate keys periodically
- Use separate keys for dev/staging/production

### 4.2 Database Credentials

**Requirement:** Database credentials protected with platform secrets management.

**Enforcement:**
- Environment variables (local dev)
- Supabase service role keys (server-side only)
- Connection strings never exposed to frontend
- Read-only database user for reporting if needed

### 4.3 Authentication Tokens

**Requirement:** JWT tokens for session management.

**Enforcement:**
- Short-lived access tokens (15 minutes)
- Refresh tokens (7 days, stored securely)
- HttpOnly cookies or secure localStorage
- Token signature verification
- Token expiry enforcement

### 4.4 Secrets Management

**Development:**
- `.env` files (gitignored)
- Never commit `.env` to repository

**Staging/Production:**
- Railway environment variables
- Vercel environment variables
- Supabase secrets dashboard

**Secret Rotation:**
- Rotate API keys quarterly
- Rotate JWT signing key on compromise
- Rotate database passwords quarterly

---

## 5. Authentication & Authorization

### 5.1 Authentication

**Phase 1 (MVP):**
- Email + password authentication
- JWT bearer tokens
- Session management

**Requirements:**
- Password hashing (bcrypt, Argon2)
- Minimum password complexity (8+ chars, mixed case, numbers)
- Account lockout after 5 failed attempts (15 min cooldown)
- No password storage in logs or error messages

**Future Enhancements:**
- Multi-factor authentication (TOTP)
- Single sign-on (OAuth 2.0)
- Hardware token support

### 5.2 Authorization

**Phase 1 (MVP):**
- Role: Investigator (full access to own cases)

**Future:**
- Admin: System administration, user management
- Investigator: Case creation, investigation
- Viewer: Read-only access to assigned cases

**Enforcement:**
- Authorization checks at API layer
- Database row-level security (Supabase RLS)
- Case ownership validation
- No client-side authorization logic

### 5.3 Session Management

**Requirements:**
- JWT tokens with short expiry
- Refresh token rotation
- Logout invalidates tokens
- Concurrent session limit (optional)

---

## 6. Data Protection

### 6.1 Data Classification

| Classification | Examples | Protection |
|----------------|----------|------------|
| Secret | API keys, DB credentials, JWT signing keys | Environment variables, never logged, encrypted at rest |
| Confidential | Case data, investigator identity, evidence notes | Encrypted at rest, encrypted in transit, access-controlled |
| Internal | Blockchain transaction data, entity registry | Access-controlled, encrypted in transit |
| Public | Documentation, aggregated statistics | No special protection |

### 6.2 Encryption

**In Transit:**
- HTTPS/TLS 1.3 for all API communication
- No HTTP fallback
- HSTS headers enforced
- Certificate pinning (future consideration)

**At Rest:**
- Database encryption (Supabase built-in)
- Encrypted backups
- No plain-text secrets in configuration files

### 6.3 PII Handling

**Minimize PII Collection:**
- Collect only necessary investigator information (name, email, role)
- Do NOT collect unnecessary personal information
- Blockchain addresses are not PII (public data)

**PII Protection:**
- Investigator emails encrypted at rest
- No PII in logs
- No PII in error messages exposed to frontend
- GDPR/privacy-by-design principles

### 6.4 Demo Data Separation

**Requirement:** Demo investigations MUST be clearly separated from production cases.

**Enforcement:**
- `is_demo` flag on case records
- Demo cases visible to all users (educational)
- Production cases visible only to owner/authorized users
- Clear UI labeling: "DEMO INVESTIGATION"

---

## 7. API Security

### 7.1 Authentication

**Requirement:** All API endpoints (except `/health`) require authentication.

**Enforcement:**
- JWT bearer token in `Authorization: Bearer <token>` header
- Token validation middleware
- 401 Unauthorized on missing/invalid token

### 7.2 Authorization

**Requirement:** Verify user has access to requested resource.

**Enforcement:**
- Case ownership validation
- User role checks
- 403 Forbidden on unauthorized access

### 7.3 Input Validation

**Requirement:** Validate all inputs at API boundary.

**Enforcement:**
- Pydantic schema validation (backend)
- Type checking (TypeScript frontend)
- Blockchain address format validation
- Transaction hash format validation
- Reject malformed requests (400 Bad Request)

**Protection Against:**
- SQL injection (use parameterized queries)
- Command injection (sanitize shell inputs)
- Path traversal (validate file paths)
- XSS (sanitize user-generated content)

### 7.4 Rate Limiting

**Requirement:** Prevent API abuse and DDoS.

**Enforcement:**
- Per-IP rate limits (100 requests/minute)
- Per-user rate limits (1000 requests/hour)
- Blockchain API rate limits (respect provider limits)
- 429 Too Many Requests on limit exceeded

### 7.5 CORS Policy

**Requirement:** Restrict cross-origin requests.

**Enforcement:**
- Allow only frontend origin (https://ledgerlens.app)
- No wildcard CORS in production
- Development: localhost:3000 allowed

### 7.6 Error Handling

**Requirement:** Do not expose sensitive information in error messages.

**Enforcement:**
- Generic error messages to client
- Detailed errors logged server-side only
- No stack traces in production API responses
- No database schema details in errors

---

## 8. Blockchain Provider Security

### 8.1 API Key Protection

**Requirement:** Blockchain API keys never exposed to frontend.

**Enforcement:**
- Backend proxies all blockchain requests
- Frontend calls `/api/v1/trace`, not Alchemy directly
- API keys in environment variables only

### 8.2 Request Sanitization

**Requirement:** Validate blockchain addresses before querying providers.

**Enforcement:**
- Address format validation (regex, checksum)
- Transaction hash validation
- Reject invalid formats before external API call

### 8.3 Provider Failure Handling

**Requirement:** Handle provider failures gracefully.

**Enforcement:**
- Timeout limits (30 seconds)
- Retry logic with exponential backoff
- Fallback to secondary provider (Etherscan if Alchemy fails)
- Return structured error states (PROVIDER_TIMEOUT, PROVIDER_UNAVAILABLE)

### 8.4 Rate Limit Management

**Requirement:** Respect provider rate limits.

**Enforcement:**
- Track request counts per provider
- Cache immutable blockchain data (transactions, blocks)
- Implement request queuing
- Alert on approaching rate limits

---

## 9. Frontend Security

### 9.1 XSS Prevention

**Requirement:** Prevent cross-site scripting.

**Enforcement:**
- React auto-escapes user content
- No `dangerouslySetInnerHTML` except for sanitized report HTML
- Content Security Policy (CSP) headers
- Sanitize user-generated notes before display

### 9.2 Token Storage

**Requirement:** Securely store JWT tokens.

**Options:**
1. HttpOnly cookies (recommended for MVP)
2. Secure localStorage (with XSS protections)

**Enforcement:**
- No token exposure to JavaScript if using HttpOnly cookies
- Secure flag on cookies (HTTPS only)
- SameSite=Strict to prevent CSRF

### 9.3 Sensitive Data Handling

**Requirement:** Do not log sensitive data in browser console.

**Enforcement:**
- Remove debug logs in production builds
- No API keys in frontend code
- No full case data logged to console

---

## 10. Report Security

### 10.1 Report Sanitization

**Requirement:** Prevent XSS in exported HTML reports.

**Enforcement:**
- Sanitize investigator notes before inclusion in HTML
- Use templating engine with auto-escaping
- Content Security Policy in report HTML
- No inline JavaScript in reports

### 10.2 Report Access Control

**Requirement:** Reports accessible only to authorized investigators.

**Enforcement:**
- Report generation requires authentication
- Report download requires case ownership
- Report links are non-guessable (UUID-based)
- Optional: Expiring report links

---

## 11. Database Security

### 11.1 Access Control

**Requirement:** Least-privilege database access.

**Enforcement:**
- Backend uses service role (full access)
- Frontend uses anon key (minimal access)
- Row-level security (Supabase RLS) for case ownership
- No direct database access from frontend

### 11.2 SQL Injection Prevention

**Requirement:** Prevent SQL injection.

**Enforcement:**
- Use parameterized queries (SQLAlchemy, Supabase client)
- No raw SQL concatenation with user input
- ORM usage preferred
- Validate inputs before queries

### 11.3 Backup & Recovery

**Requirement:** Protect case data with backups.

**Enforcement:**
- Automated daily backups (Supabase)
- Encrypted backup storage
- Backup retention (30 days)
- Tested restore procedure

---

## 12. Logging & Monitoring

### 12.1 Security Event Logging

**Log Events:**
- User login/logout
- Failed authentication attempts
- Authorization failures
- Case creation/access
- Report generation
- Blockchain API requests (sanitized)
- Configuration changes

**Log Format:**
```json
{
  "timestamp": "2026-09-22T14:05:20.852Z",
  "level": "INFO",
  "event": "user_login",
  "user_id": "uuid",
  "ip_address": "1.2.3.4",
  "user_agent": "Mozilla/5.0..."
}
```

### 12.2 Sensitive Data in Logs

**Never Log:**
- Passwords
- API keys (full)
- JWT tokens (full)
- Database credentials
- Private keys (system never handles these)

**Redaction:**
- Log API key prefix only (e.g., "alch_abc...***")
- Log user email as "u***@domain.com"
- Sanitize stack traces before logging

### 12.3 Monitoring

**Alerts:**
- Multiple failed login attempts (5+ in 5 min)
- Unusual API usage patterns
- Provider API failures
- Database connection failures
- Disk space warnings

---

## 13. Dependency Security

### 13.1 Dependency Management

**Requirement:** Keep dependencies up-to-date and secure.

**Enforcement:**
- Use `npm audit` (frontend) and `pip-audit` (backend)
- Pin dependency versions
- Review security advisories
- Update critical vulnerabilities within 7 days

### 13.2 Supply Chain Security

**Requirement:** Verify dependency integrity.

**Enforcement:**
- Lock files (package-lock.json, poetry.lock)
- Use official package repositories (npm, PyPI)
- Review dependency licenses
- Avoid dependencies with known vulnerabilities

---

## 14. Security Review Gates

### 14.1 Phase 0 (Foundation)
- [x] Secrets management strategy defined
- [x] Authentication approach documented
- [x] API security requirements specified

### 14.2 Phase 1 (Case Foundation)
- [ ] Authentication implemented
- [ ] Authorization implemented
- [ ] Input validation implemented
- [ ] Database RLS configured

### 14.3 Phase 2 (Blockchain Foundation)
- [ ] API key protection verified
- [ ] Provider request sanitization implemented
- [ ] Rate limit handling implemented

### 14.4 Phase 3 (Investigation UI)
- [ ] XSS prevention verified
- [ ] Token storage implemented securely
- [ ] CORS policy configured

### 14.5 Phase 6 (Reporting)
- [ ] Report sanitization implemented
- [ ] Report access control verified

### 14.6 Phase 7 (Hardening)
- [ ] Security audit conducted
- [ ] Penetration testing (if feasible)
- [ ] Vulnerability remediation
- [ ] Security documentation reviewed

---

## 15. Incident Response

### 15.1 Security Incident Definition

**Incidents:**
- Unauthorized access to case data
- API key compromise
- Database credential leak
- Successful attack (XSS, SQL injection, etc.)
- DDoS attack

### 15.2 Response Procedure

1. **Detect:** Monitoring/alerting identifies incident
2. **Contain:** Disable compromised credentials, block attacker IP
3. **Investigate:** Review logs, identify scope
4. **Remediate:** Patch vulnerability, rotate credentials
5. **Document:** Incident report, lessons learned
6. **Notify:** Inform affected users if data breach

### 15.3 Credential Compromise Response

**If API key compromised:**
1. Immediately rotate key with provider
2. Update environment variables
3. Redeploy backend
4. Review logs for unauthorized usage
5. Monitor for billing anomalies

**If database credential compromised:**
1. Immediately rotate password
2. Update environment variables
3. Review access logs
4. Audit data access
5. Consider full backup restoration if integrity uncertain

---

## 16. Compliance Considerations

### 16.1 GDPR (Future)

**If European users:**
- Data processing agreements
- Right to access (investigator data)
- Right to deletion (investigator accounts)
- Data breach notification (<72 hours)

### 16.2 Law Enforcement Use

**Considerations:**
- Chain of custody for evidence
- Audit trail for case access
- Data retention policies
- Authorized access logging

---

## 17. Security Testing

### 17.1 Testing Requirements

**Unit Tests:**
- Authentication logic
- Authorization checks
- Input validation
- Sanitization functions

**Integration Tests:**
- API authentication/authorization
- Rate limiting
- Token expiry

**Security Tests:**
- SQL injection attempts
- XSS payload attempts
- Authentication bypass attempts
- CSRF attempts

### 17.2 Security Tools

**Recommended:**
- `npm audit` / `pip-audit` (dependency scanning)
- `bandit` (Python static analysis)
- `eslint-plugin-security` (JavaScript static analysis)
- OWASP ZAP (penetration testing, Phase 7)

---

## 18. Security Responsibilities

### 18.1 By Phase

**Phase 0-1:** MASTER, System Architect  
**Phase 1-5:** Backend Engineer, Database Engineer (implement security controls)  
**Phase 6-7:** Security Engineer (review, audit)

### 18.2 Ongoing

**All Engineers:**
- Follow secure coding practices
- Validate inputs
- Never commit secrets
- Review PRs for security issues

**MASTER:**
- Enforce security review gates
- Approve security-sensitive changes
- Coordinate incident response

---

## Security Status

**Phase 0:** Security model documented ✅  
**Phase 1:** Implementation pending  
**Phase 7:** Security audit pending

---

**Document Status:** Initial security specification  
**Approval Required:** MASTER / CTO  
**Dependencies:** ARCHITECTURE.md, DATA_MODEL.md
