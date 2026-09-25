"""Phase 7 — security tests for SEC-01 (authentication), SEC-02 (authorization),
SEC-04 (CORS) and SEC-06 (framework docs exposure).

These tests deliberately run WITHOUT the shared authenticated-principal
override from tests/conftest.py so that real enforcement behaviour is asserted.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from app.db.database import get_db
from app.db.models import Case, Investigator, ReportRecord
from app.main import app
from app.services.auth.deps import get_current_principal
from app.services.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.api.v1.cases import MOCK_INVESTIGATOR_ID
from tests.conftest import TEST_PRINCIPAL


OTHER_INVESTIGATOR_ID = uuid4()
CASE_ID = uuid4()
REPORT_ID = uuid4()
PASSWORD = "CorrectHorse9Battery"


class _QueryResult:
    def __init__(self, scalar=None, rows=None):
        self._scalar = scalar
        self._rows = rows if rows is not None else []

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return self

    def all(self):
        return self._rows


class _StubDB:
    def __init__(self, scalar=None, rows=None):
        self._scalar = scalar
        self._rows = rows if rows is not None else []

    async def execute(self, *args, **kwargs):
        return _QueryResult(self._scalar, self._rows)

    async def commit(self):
        return None

    def add(self, obj):
        return None

    async def flush(self):
        return None

    async def refresh(self, obj):
        return None


def _stub_db_fixture():
    async def _stub():
        yield _StubDB()

    return _stub


def _make_investigator() -> Investigator:
    return Investigator(
        investigator_id=uuid4(),
        username="jane.investigator@agency.gov",
        email="jane.investigator@agency.gov",
        password_hash=hash_password(PASSWORD),
        full_name="Jane Investigator",
        role="investigator",
        active=True,
        created_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        last_login=None,
    )


def _case_owned_by(investigator_id: UUID) -> Case:
    return Case(
        case_id=CASE_ID,
        case_number="LL-2026-0007",
        title="Ownership fixture",
        reported_wallet_address="0x" + "3" * 40,
        blockchain="ethereum",
        fraud_type="investment_scam",
        investigator_id=investigator_id,
        status="active",
        created_at=datetime(2026, 9, 21, tzinfo=timezone.utc),
        updated_at=datetime(2026, 9, 21, tzinfo=timezone.utc),
    )


@pytest.fixture
def without_principal_override(authenticated_principal):
    app.dependency_overrides.pop(get_current_principal, None)
    yield authenticated_principal
    app.dependency_overrides[get_current_principal] = lambda: authenticated_principal


def _token(investigator_id: UUID, **kwargs) -> str:
    return create_access_token(
        investigator_id=investigator_id,
        username=kwargs.get("username", "jane.investigator@agency.gov"),
        role=kwargs.get("role", "investigator"),
        expires_minutes=kwargs.get("expires_minutes", 15),
    )


# ---------------------------------------------------------------------------
# SEC-01 — authentication
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_protected_route_rejects_missing_token(without_principal_override):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/cases")
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.asyncio
async def test_protected_route_rejects_malformed_token(without_principal_override):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/cases", headers={"Authorization": "Bearer not.a.token"}
        )
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_protected_route_rejects_expired_token(without_principal_override):
    expired = _token(MOCK_INVESTIGATOR_ID, expires_minutes=-5)
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/cases", headers={"Authorization": f"Bearer {expired}"}
        )
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "TOKEN_EXPIRED"


@pytest.mark.asyncio
async def test_protected_route_accepts_valid_token(without_principal_override):
    app.dependency_overrides[get_db] = _stub_db_fixture()
    token = _token(MOCK_INVESTIGATOR_ID)
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/cases", headers={"Authorization": f"Bearer {token}"}
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_health_and_root_remain_public(without_principal_override):
    async with AsyncClient(app=app, base_url="http://test") as client:
        health = await client.get("/health")
        root = await client.get("/")
    assert health.status_code == 200
    assert root.status_code == 200


@pytest.mark.asyncio
async def test_auth_me_requires_token(without_principal_override):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_me_returns_profile(without_principal_override):
    investigator = _make_investigator()

    async def _db():
        yield _StubDB(scalar=investigator)

    app.dependency_overrides[get_db] = _db
    token = _token(investigator.investigator_id)
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == investigator.username
    assert body["role"] == "investigator"
    assert body["investigator_id"] == str(investigator.investigator_id)


@pytest.mark.asyncio
async def test_login_success_issues_bearer_token(without_principal_override):
    investigator = _make_investigator()

    async def _db():
        yield _StubDB(scalar=investigator)

    app.dependency_overrides[get_db] = _db
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"username": investigator.username, "password": PASSWORD},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert body["investigator"]["username"] == investigator.username
    claims = decode_access_token(body["access_token"])
    assert claims["sub"] == str(investigator.investigator_id)
    assert claims["role"] == "investigator"


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(without_principal_override):
    investigator = _make_investigator()

    async def _db():
        yield _StubDB(scalar=investigator)

    app.dependency_overrides[get_db] = _db
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"username": investigator.username, "password": "WrongPassword1"},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_rejects_unknown_user(without_principal_override):
    async def _db():
        yield _StubDB(scalar=None)

    app.dependency_overrides[get_db] = _db
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"username": "nobody@agency.gov", "password": PASSWORD},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "INVALID_CREDENTIALS"


def test_password_hashing_round_trip():
    digest = hash_password(PASSWORD)
    assert digest != PASSWORD
    assert verify_password(PASSWORD, digest) is True
    assert verify_password("not-the-password", digest) is False
    assert verify_password(PASSWORD, "") is False


def test_access_token_carries_subject_and_expiry():
    claims = decode_access_token(_token(MOCK_INVESTIGATOR_ID))
    assert claims["sub"] == str(MOCK_INVESTIGATOR_ID)
    assert claims["typ"] == "access"
    assert claims["exp"] > claims["iat"]


# ---------------------------------------------------------------------------
# SEC-02 — authorization / ownership
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_case_owned_by_another_investigator_is_forbidden(without_principal_override):
    async def _db():
        yield _StubDB(scalar=_case_owned_by(OTHER_INVESTIGATOR_ID))

    app.dependency_overrides[get_db] = _db
    token = _token(TEST_PRINCIPAL.investigator_id, username=TEST_PRINCIPAL.username)
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/cases/{CASE_ID}", headers={"Authorization": f"Bearer {token}"}
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert response.status_code == 403
    assert response.json()["detail"]["error"]["code"] == "CASE_ACCESS_DENIED"


@pytest.mark.asyncio
async def test_case_owned_by_caller_is_readable(without_principal_override):
    async def _db():
        yield _StubDB(scalar=_case_owned_by(MOCK_INVESTIGATOR_ID))

    app.dependency_overrides[get_db] = _db
    token = _token(MOCK_INVESTIGATOR_ID, username=TEST_PRINCIPAL.username)
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/cases/{CASE_ID}", headers={"Authorization": f"Bearer {token}"}
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert response.status_code == 200
    assert response.json()["case_id"] == str(CASE_ID)


@pytest.mark.asyncio
async def test_report_download_is_forbidden_for_non_owner(without_principal_override):
    from app.services.reporting import get_report_store

    record = ReportRecord(
        report_id=REPORT_ID,
        case_id=CASE_ID,
        report_type="brief",
        format="json",
        content=b"{}",
        file_path=None,
        generated_by=OTHER_INVESTIGATOR_ID,
        generated_at=datetime(2026, 9, 22, tzinfo=timezone.utc),
    )

    class _Store:
        async def get_report(self, report_id):
            return record

    async def _db():
        yield _StubDB(scalar=_case_owned_by(OTHER_INVESTIGATOR_ID))

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_report_store] = lambda: _Store()
    token = _token(MOCK_INVESTIGATOR_ID, username=TEST_PRINCIPAL.username)
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/reports/{REPORT_ID}/download",
                headers={"Authorization": f"Bearer {token}"},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_report_store, None)
    assert response.status_code == 403
    assert response.json()["detail"]["error"]["code"] == "CASE_ACCESS_DENIED"


@pytest.mark.asyncio
async def test_copilot_endpoint_enforces_case_ownership(without_principal_override):
    from app.api.v1.copilot import get_copilot_engine

    async def _db():
        yield _StubDB(scalar=_case_owned_by(OTHER_INVESTIGATOR_ID))

    class _UnusedEngine:
        pass

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_copilot_engine] = lambda: _UnusedEngine()
    token = _token(MOCK_INVESTIGATOR_ID, username=TEST_PRINCIPAL.username)
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/cases/{CASE_ID}/copilot/ask",
                json={"question": "What happened?"},
                headers={"Authorization": f"Bearer {token}"},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_copilot_engine, None)
    assert response.status_code == 403
    assert response.json()["detail"]["error"]["code"] == "CASE_ACCESS_DENIED"


# ---------------------------------------------------------------------------
# SEC-04 / SEC-06 — configuration hardening
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_api_docs_are_disabled_by_default(without_principal_override):
    async with AsyncClient(app=app, base_url="http://test") as client:
        docs = await client.get("/docs")
        redoc = await client.get("/redoc")
        openapi = await client.get("/openapi.json")
    assert docs.status_code == 404
    assert redoc.status_code == 404
    assert openapi.status_code == 404


@pytest.mark.asyncio
async def test_cors_rejects_unknown_origin(without_principal_override):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/health", headers={"Origin": "https://evil.example"}
        )
    assert response.headers.get("access-control-allow-origin") is None


@pytest.mark.asyncio
async def test_cors_allows_configured_frontend_origin(without_principal_override):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/health", headers={"Origin": "http://localhost:3000"}
        )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
