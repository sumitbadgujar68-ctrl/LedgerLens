# LedgerLens Development Standards

**Last Updated:** 2026-09-22T14:13:21Z  
**Phase:** PHASE 0 — FOUNDATION  
**Status:** Initial Standards

---

## 1. Overview

This document defines coding standards, testing strategies, and engineering practices for LedgerLens development.

---

## 2. Python Standards (Backend)

### 2.1 Code Formatting

**Tool:** [Black](https://black.readthedocs.io/)

```bash
black backend/ --line-length 100
```

**Configuration:** `.black` or `pyproject.toml`
```toml
[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'
```

**Rationale:** Consistent, opinionated formatting eliminates style debates.

### 2.2 Linting

**Tool:** [Ruff](https://docs.astral.sh/ruff/)

```bash
ruff check backend/
```

**Configuration:** `ruff.toml` or `pyproject.toml`
```toml
[tool.ruff]
line-length = 100
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
    "S",   # flake8-bandit (security)
]
ignore = [
    "E501", # line too long (handled by black)
]
```

**Rationale:** Fast, comprehensive linting with security checks.

### 2.3 Type Checking

**Tool:** [mypy](https://mypy.readthedocs.io/)

```bash
mypy backend/ --strict
```

**Configuration:** `mypy.ini` or `pyproject.toml`
```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_unimported = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
```

**Rationale:** Type safety prevents runtime errors, improves IDE support.

### 2.4 Import Sorting

**Tool:** Ruff (includes isort functionality)

**Order:**
1. Standard library imports
2. Third-party imports
3. Local application imports

**Example:**
```python
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.services.blockchain import EthereumAdapter
from backend.models.transaction import Transaction
```

### 2.5 Docstrings

**Standard:** Google-style docstrings

**Example:**
```python
def normalize_transaction(
    raw_tx: dict,
    blockchain: str,
    provider: str
) -> Transaction:
    """Normalize chain-specific transaction to canonical model.

    Args:
        raw_tx: Raw transaction data from provider
        blockchain: Blockchain identifier (ethereum, tron, etc.)
        provider: Provider name (alchemy, etherscan, etc.)

    Returns:
        Normalized Transaction object

    Raises:
        ValidationError: If transaction data is invalid
        ProviderError: If provider data is malformed
    """
    pass
```

### 2.6 Async/Await

- Use `async`/`await` for I/O-bound operations (blockchain API calls, database queries)
- Use synchronous code for CPU-bound operations (risk calculations, pattern detection)
- FastAPI route handlers should be `async def` when calling async services

**Example:**
```python
@router.get("/cases/{case_id}/transactions")
async def get_case_transactions(case_id: str) -> list[Transaction]:
    return await transaction_service.get_by_case(case_id)
```

---

## 3. TypeScript/React Standards (Frontend)

### 3.1 Code Formatting

**Tool:** [Prettier](https://prettier.io/)

```bash
prettier --write frontend/
```

**Configuration:** `.prettierrc`
```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": false,
  "printWidth": 100,
  "tabWidth": 2,
  "arrowParens": "always"
}
```

### 3.2 Linting

**Tool:** [ESLint](https://eslint.org/)

```bash
eslint frontend/ --ext .ts,.tsx
```

**Configuration:** `.eslintrc.json`
```json
{
  "extends": [
    "next/core-web-vitals",
    "plugin:@typescript-eslint/recommended",
    "prettier"
  ],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-explicit-any": "error",
    "no-console": ["warn", { "allow": ["warn", "error"] }]
  }
}
```

### 3.3 TypeScript Configuration

**Strict mode enabled:**
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

### 3.4 Component Standards

**Functional components with TypeScript:**
```typescript
interface CaseCardProps {
  caseId: string;
  caseNumber: string;
  blockchain: string;
  status: CaseStatus;
  onSelect: (caseId: string) => void;
}

export const CaseCard: React.FC<CaseCardProps> = ({
  caseId,
  caseNumber,
  blockchain,
  status,
  onSelect,
}) => {
  return (
    // Component JSX
  );
};
```

**File naming:**
- Components: `PascalCase.tsx` (e.g., `CaseCard.tsx`)
- Utilities: `camelCase.ts` (e.g., `formatAddress.ts`)
- Hooks: `useHookName.ts` (e.g., `useCase.ts`)

---

## 4. Testing Strategy

### 4.1 Backend Testing (Python)

**Framework:** [pytest](https://pytest.org/)

**Structure:**
```
tests/
├── unit/
│   ├── services/
│   │   ├── test_transaction_normalizer.py
│   │   ├── test_risk_engine.py
│   │   └── test_vasp_attribution.py
│   └── models/
├── integration/
│   ├── test_blockchain_adapters.py
│   ├── test_api_endpoints.py
│   └── test_database.py
└── e2e/
    └── test_investigation_workflow.py
```

**Test naming:**
```python
def test_normalize_ethereum_transaction_success():
    pass

def test_normalize_ethereum_transaction_invalid_address_raises_error():
    pass
```

**Fixtures:**
```python
@pytest.fixture
def sample_ethereum_transaction():
    return {
        "hash": "0x123...",
        "blockNumber": 12345678,
        # ...
    }
```

**Mocking blockchain providers:**
```python
@pytest.mark.asyncio
async def test_ethereum_adapter_fetch_transaction(mocker):
    mock_provider = mocker.patch("backend.services.blockchain.AlchemyProvider")
    mock_provider.fetch_transaction.return_value = {...}
    # Test adapter logic
```

**Coverage target:** 80% minimum

**Run tests:**
```bash
pytest tests/ --cov=backend --cov-report=html
```

### 4.2 Frontend Testing (TypeScript/React)

**Framework:** [Jest](https://jestjs.io/) + [React Testing Library](https://testing-library.com/react)

**Structure:**
```
frontend/
├── components/
│   ├── CaseCard.tsx
│   └── CaseCard.test.tsx
├── hooks/
│   ├── useCase.ts
│   └── useCase.test.ts
└── utils/
    ├── formatAddress.ts
    └── formatAddress.test.ts
```

**Example:**
```typescript
import { render, screen } from "@testing-library/react";
import { CaseCard } from "./CaseCard";

describe("CaseCard", () => {
  it("renders case number and blockchain", () => {
    render(
      <CaseCard
        caseId="123"
        caseNumber="CASE-2024-001"
        blockchain="ethereum"
        status="active"
        onSelect={jest.fn()}
      />
    );
    expect(screen.getByText("CASE-2024-001")).toBeInTheDocument();
    expect(screen.getByText("ethereum")).toBeInTheDocument();
  });
});
```

**Coverage target:** 70% minimum

**Run tests:**
```bash
npm test -- --coverage
```

### 4.3 E2E Testing

**Framework:** [Playwright](https://playwright.dev/) (Phase 3+)

**Scope:**
- Complete investigation workflow
- Case creation → trace → graph → attribution → report
- Critical user paths only (not exhaustive)

---

## 5. Git Workflow

### 5.1 Branch Strategy

**Main branch:** `main` (or `master`)

**Feature branches:**
```
feature/case-intake
feature/ethereum-adapter
feature/graph-visualization
fix/transaction-normalization-bug
```

**Branch naming:**
- `feature/` — new features
- `fix/` — bug fixes
- `docs/` — documentation updates
- `refactor/` — code refactoring

### 5.2 Commit Messages

**Format:** Conventional Commits

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation
- `refactor:` — code refactoring
- `test:` — test additions/changes
- `chore:` — build/tooling changes

**Examples:**
```
feat(blockchain): implement Ethereum adapter with Alchemy provider

Adds EthereumAdapter with provider abstraction layer.
Supports transaction history, token transfers, and normalization.

Closes #42

---

fix(risk): correct peel chain pattern detection threshold

The peel chain detection was triggering false positives for
legitimate exchange consolidation patterns.

---

docs(architecture): update blockchain adapter sequence diagram
```

### 5.3 Pull Request Process

1. Create feature branch from `main`
2. Implement changes with tests
3. Run linters and tests locally
4. Commit with conventional commit messages
5. Push to remote
6. Create pull request with description
7. Wait for CI checks to pass
8. Request review from MASTER or relevant specialist
9. Address review feedback
10. Merge after approval

---

## 6. Environment Configuration

### 6.1 Environment Variables

**Never commit:** `.env`, `.env.local`, `secrets/`

**Required environment variables:**

**Backend (`backend/.env`):**
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ledgerlens
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx

# Blockchain Providers
ALCHEMY_API_KEY=xxx
ETHERSCAN_API_KEY=xxx
TRONGRID_API_KEY=xxx

# Security
JWT_SECRET_KEY=xxx
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
```

**Frontend (`frontend/.env.local`):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

**Development defaults:** Use `.env.example` files with placeholder values.

### 6.2 Configuration Management

**Backend:** Use `pydantic-settings` for typed configuration

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    alchemy_api_key: str
    jwt_secret_key: str
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 7. Logging Strategy

### 7.1 Backend Logging

**Library:** Python `logging` module

**Format:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

**Log levels:**
- `DEBUG` — Development debugging
- `INFO` — Normal operations (case created, trace started)
- `WARNING` — Recoverable issues (provider timeout, rate limit)
- `ERROR` — Errors requiring attention (invalid input, provider failure)
- `CRITICAL` — System failures

**Sensitive data:** Never log API keys, secrets, or PII

**Example:**
```python
logger.info(f"Starting trace for case {case_id}, wallet {wallet_address[:10]}...")
logger.warning(f"Provider timeout for {provider_name}, using fallback")
logger.error(f"Failed to normalize transaction {tx_hash}: {error}")
```

### 7.2 Frontend Logging

**Development:** `console.log`, `console.warn`, `console.error`

**Production:** Consider third-party service (Sentry, LogRocket) in Phase 6+

---

## 8. Error Handling

### 8.1 Backend Error Handling

**Custom exceptions:**
```python
class LedgerLensError(Exception):
    """Base exception for LedgerLens."""

class ProviderError(LedgerLensError):
    """Blockchain provider error."""

class ValidationError(LedgerLensError):
    """Input validation error."""

class AttributionError(LedgerLensError):
    """VASP attribution error."""
```

**FastAPI exception handlers:**
```python
@app.exception_handler(ProviderError)
async def provider_error_handler(request: Request, exc: ProviderError):
    return JSONResponse(
        status_code=503,
        content={
            "error": "PROVIDER_ERROR",
            "message": str(exc),
            "details": {"provider": exc.provider_name}
        }
    )
```

**Graceful degradation:** If provider fails, log error and return partial results with clear status indicators.

### 8.2 Frontend Error Handling

**Error boundaries:** Catch React component errors

**API error handling:**
```typescript
try {
  const response = await fetch(`/api/v1/cases/${caseId}`);
  if (!response.ok) {
    const error = await response.json();
    throw new APIError(error.message, error.error);
  }
  return await response.json();
} catch (error) {
  if (error instanceof APIError) {
    // Display user-friendly error
  } else {
    // Log unexpected error
  }
}
```

---

## 9. Code Review Checklist

**Before requesting review:**
- [ ] Code follows formatting standards (black, prettier)
- [ ] Linters pass (ruff, eslint)
- [ ] Type checking passes (mypy, tsc)
- [ ] Tests written and passing
- [ ] No secrets committed
- [ ] Documentation updated
- [ ] Commit messages follow convention

**Reviewer checklist:**
- [ ] Architecture respects module boundaries
- [ ] No duplicate logic
- [ ] Error handling appropriate
- [ ] Security implications considered
- [ ] Performance reasonable
- [ ] Code readable and maintainable

---

## 10. CI/CD Pipeline (Phase 0 Foundation)

**GitHub Actions / GitLab CI workflow:**

```yaml
name: CI

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: black --check backend/
      - run: ruff check backend/
      - run: mypy backend/
      - run: pytest tests/ --cov

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run lint
      - run: npm run type-check
      - run: npm test -- --coverage
```

**Deployment:** Phase 6+

---

## 11. Dependencies Management

### 11.1 Python Dependencies

**Tool:** `pip` with `requirements.txt` (initial) or `poetry` (future consideration)

**Structure:**
```
requirements.txt          # Production dependencies
requirements-dev.txt      # Development dependencies
```

**Version pinning:** Pin major versions, allow minor/patch updates

```txt
fastapi>=0.104.0,<1.0.0
pydantic>=2.4.0,<3.0.0
```

**Security:** Run `pip-audit` periodically

### 11.2 Node Dependencies

**Tool:** `npm` (or `yarn`/`pnpm` if preferred)

**Lock file:** Commit `package-lock.json`

**Security:** Run `npm audit` regularly

---

## 12. Documentation Standards

**Code documentation:**
- Python: Google-style docstrings
- TypeScript: JSDoc comments

**Architecture documentation:**
- ADRs for decisions (docs/DECISIONS.md)
- Architecture diagrams (ASCII/text or tools like Mermaid)

**API documentation:**
- FastAPI auto-generates OpenAPI/Swagger docs
- Keep docs/API_CONTRACT.md conceptual overview

**User documentation:** Phase 6+ (deployment guide, user manual)

---

## 13. Performance Guidelines

**Backend:**
- Use async/await for I/O operations
- Implement database query optimization (indexes, pagination)
- Use connection pooling for database/blockchain providers
- Cache expensive computations where appropriate

**Frontend:**
- Use React.memo for expensive components
- Implement virtual scrolling for large transaction lists
- Lazy load graph visualization data
- Optimize bundle size

**Defer optimization:** Don't prematurely optimize. Measure first.

---

## 14. Accessibility Standards

**Frontend:**
- Semantic HTML
- ARIA labels where necessary
- Keyboard navigation support
- Color contrast compliance (WCAG 2.1 AA minimum)
- Screen reader testing

**Testing:** Use `jest-axe` for automated accessibility testing

---

## Enforcement

- **Pre-commit hooks:** Run formatters/linters automatically (Phase 1+)
- **CI pipeline:** Block PRs that fail linting/tests
- **Code reviews:** Enforce standards through review process
- **MASTER oversight:** Verify standards compliance during integration

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2026-09-22 | 1.0 | Initial development standards |
