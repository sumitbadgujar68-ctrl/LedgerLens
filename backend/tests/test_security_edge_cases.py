"""Phase 7 Step 3 — regression edge/error scenarios (TASK-P7-003).

Complements tests/test_security_auth.py with the remaining audit §8
requirements (docs/PHASE_7_SECURITY_AUDIT.md) and Phase 6/7 error paths:

- §8.3 input validation: malformed and oversized payloads on live routes
- §8.4 sanitization: download header safety (renderer HTML escaping and
  provider API-key redaction are covered by tests/test_report_rendering.py
  and tests/test_blockchain.py respectively)
- §8.8 SQL injection: hostile payloads as path/query parameters, plus the
  bound-parameter structure of every string filter that reaches a query
- §8.9 XSS: hostile text entering through the API and leaving through the
  generated HTML report / JSON export
- Phase 6/7 error scenarios: unknown case ids, no-trace risk paths,
  unknown trace ids, documented error envelopes

No production code is modified by this suite.
"""

import re
from typing import Any, List, Optional
from urllib.parse import quote
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app.api.v1.cases import MOCK_INVESTIGATOR_ID
from app.db.database import get_db
from app.db.models import Case, RiskScoreRecord, TraceRun
from app.main import app
from app.services.auth.deps import get_current_principal
from app.services.reporting import deserialize_report
from tests.conftest import TEST_PRINCIPAL
from tests.test_report_aggregation import CASE, StubGrounding
from tests.test_report_api import (
    CASE_ID,
    CASE_NUMBER,
    cleanup_overrides,
    fixture_generator,
    install_overrides,
    make_case,
)
from tests.test_report_rendering import XSS_PAYLOAD, make_store

VALID_CASE_PAYLOAD = {
    "title": "Regression fixture case",
    "reported_wallet_address": "0x" + "1" * 40,
    "blockchain": "ethereum",
    "fraud_type": "investment_scam",
}

SQLI_PAYLOAD = "0x' OR '1'='1'; DROP TABLE cases;--"

POSTGRES_DIALECT = postgresql.dialect()


# ----------------------------------------------------------------------
# Test doubles
# ----------------------------------------------------------------------


def _compiled(stmt: Any):
    return stmt.compile(dialect=POSTGRES_DIALECT)


class CaseOnlyStubDB:
    """Session double: answers Case/TraceRun reads, empties every other table.

    Hostile string parameters flow through the same statement-building path a
    real session would take; only execution is replaced.
    """

    def __init__(self, case: Optional[Case], trace: Optional[TraceRun] = None) -> None:
        self.case = case
        self.trace = trace

    async def execute(self, stmt, *args, **kwargs):
        compiled = _compiled(stmt)
        sql = str(compiled)
        values = {str(v) for v in compiled.params.values()}
        rows: List[Any] = []

        if "FROM cases" in sql and self.case is not None:
            if str(self.case.case_id) in values:
                rows = [self.case]
        elif sql.lstrip().upper().startswith("UPDATE CASES") and self.case is not None:
            # Emulate the write so subsequent reads observe the new values.
            for name, value in compiled.params.items():
                for attribute in ("title", "investigator_notes", "status"):
                    if name.startswith(attribute):
                        setattr(self.case, attribute, value)
        elif "FROM trace_runs" in sql and self.trace is not None and self.case is not None:
            foreign_ids = [
                v
                for v in values
                if _is_uuid(v) and v not in {str(self.case.case_id), str(self.trace.trace_id)}
            ]
            if str(self.case.case_id) in values and not foreign_ids:
                rows = [self.trace]

        single = rows[0] if rows else None
        many = list(rows)

        class _Result:
            def scalar_one_or_none(self_inner):
                return single

            def scalars(self_inner):
                class _Scalars:
                    def all(self_inner2):
                        return many

                return _Scalars()

        return _Result()

    def add(self, obj: Any) -> None:
        return None

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def refresh(self, obj: Any) -> None:
        return None


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except ValueError:
        return False


def install_case_db(case: Optional[Case], trace: Optional[TraceRun] = None) -> None:
    async def _override():
        yield CaseOnlyStubDB(case, trace)

    app.dependency_overrides[get_db] = _override


def sample_trace(case: Case) -> TraceRun:
    return TraceRun(
        trace_id=uuid4(),
        case_id=case.case_id,
        start_wallet_address=case.reported_wallet_address,
        blockchain="ethereum",
        direction="outbound",
        status="completed",
    )


async def _post_case(payload):
    async with AsyncClient(app=app, base_url="http://test") as client:
        return await client.post("/api/v1/cases", json=payload)


# ----------------------------------------------------------------------
# §8.3 Input validation (API level)
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_case_create_rejects_empty_title():
    response = await _post_case({**VALID_CASE_PAYLOAD, "title": ""})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_case_create_rejects_title_over_documented_max():
    response = await _post_case({**VALID_CASE_PAYLOAD, "title": "T" * 501})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_case_create_rejects_oversized_payload():
    response = await _post_case({**VALID_CASE_PAYLOAD, "title": "T" * 100_000})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_case_create_rejects_unknown_blockchain():
    response = await _post_case({**VALID_CASE_PAYLOAD, "blockchain": "dogechain"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_case_create_rejects_unknown_fraud_type():
    response = await _post_case({**VALID_CASE_PAYLOAD, "fraud_type": "get_rich_quick"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_case_update_rejects_invalid_status():
    install_case_db(make_case())
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.put(
                f"/api/v1/cases/{CASE_ID}", json={"status": "whatever-i-want"}
            )
    finally:
        cleanup_overrides()
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_malformed_case_id_returns_422():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/cases/not-a-uuid")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_malformed_risk_id_returns_422():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/cases/risk/not-a-uuid/explanation")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_cases_rejects_non_integer_limit():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/cases", params={"limit": "1 OR 1=1"})
    assert response.status_code == 422


# ----------------------------------------------------------------------
# §8.8 SQL injection attempts
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sql_injection_wallet_payload_reaches_bound_query_and_fails_closed():
    case = make_case()
    trace = sample_trace(case)
    install_case_db(case, trace)
    payload = quote(SQLI_PAYLOAD, safe="")
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/cases/{CASE_ID}/wallets/{payload}/risk"
            )
    finally:
        cleanup_overrides()

    # The hostile payload reached the risk-score filter (parameterized), no row
    # matched, and the route failed closed with a documented envelope.
    assert response.status_code == 404
    error = response.json()["detail"]["error"]
    assert error["code"] in {"GRAPH_NOT_FOUND", "NO_TRACE", "RISK_NOT_FOUND"}
    assert "sqlalchemy" not in response.text.lower()
    assert "syntax error" not in response.text.lower()


@pytest.mark.asyncio
async def test_sql_injection_username_payload_returns_401_not_500():
    install_case_db(None)
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"username": SQLI_PAYLOAD, "password": "irrelevant"},
            )
    finally:
        cleanup_overrides()

    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_sql_injection_case_id_payload_returns_422_not_500():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/cases/{quote(SQLI_PAYLOAD, safe='')}"
        )
    assert response.status_code == 422


def test_every_string_filter_is_a_bound_parameter():
    payload = SQLI_PAYLOAD

    wallet_stmt = select(RiskScoreRecord).where(
        RiskScoreRecord.wallet_address == payload
    )
    wallet_compiled = _compiled(wallet_stmt)
    assert payload in {str(v) for v in wallet_compiled.params.values()}
    assert payload not in str(wallet_compiled)

    case_stmt = select(Case).where(Case.case_id == CASE_ID)
    case_compiled = _compiled(case_stmt)
    assert str(CASE_ID) in {str(v) for v in case_compiled.params.values()}
    assert str(CASE_ID) not in str(case_compiled)

    investigator_stmt = select(Case).where(
        Case.investigator_id == MOCK_INVESTIGATOR_ID
    )
    investigator_compiled = _compiled(investigator_stmt)
    assert str(MOCK_INVESTIGATOR_ID) in {
        str(v) for v in investigator_compiled.params.values()
    }
    assert str(MOCK_INVESTIGATOR_ID) not in str(investigator_compiled)


# ----------------------------------------------------------------------
# §8.9 XSS payload attempts (API layer; renderer layer covered in
# tests/test_report_rendering.py)
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_xss_payload_round_trips_as_json_data_not_markup():
    case = make_case()
    case.updated_at = case.created_at
    install_case_db(case)
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            update = await client.put(
                f"/api/v1/cases/{CASE_ID}", json={"investigator_notes": XSS_PAYLOAD}
            )
            fetched = await client.get(f"/api/v1/cases/{CASE_ID}")
    finally:
        cleanup_overrides()

    assert update.status_code == 200
    assert fetched.status_code == 200
    assert fetched.headers["content-type"].startswith("application/json")
    assert fetched.json()["investigator_notes"] == XSS_PAYLOAD


@pytest.mark.asyncio
async def test_xss_payload_is_escaped_in_downloaded_html_report(tmp_path):
    store = make_store(tmp_path)
    session = store.db
    generator = fixture_generator()
    generator.grounding = StubGrounding(
        case={**CASE, "title": XSS_PAYLOAD, "investigator_notes": XSS_PAYLOAD}
    )
    install_overrides(make_case(), store, generator)
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            post = await client.post(
                f"/api/v1/cases/{CASE_ID}/reports",
                json={"report_type": "detailed", "format": "html"},
            )
            assert post.status_code == 202, post.text
            record = session.reports[0]
            download = await client.get(
                f"/api/v1/reports/{record.report_id}/download"
            )
    finally:
        cleanup_overrides()

    assert download.status_code == 200
    body = download.content.decode("utf-8")
    assert "<script" not in body
    assert "<img" not in body
    assert "&lt;script&gt;" in body


@pytest.mark.asyncio
async def test_xss_payload_is_preserved_verbatim_in_json_export(tmp_path):
    store = make_store(tmp_path)
    session = store.db
    generator = fixture_generator()
    generator.grounding = StubGrounding(
        case={**CASE, "title": XSS_PAYLOAD, "investigator_notes": XSS_PAYLOAD}
    )
    install_overrides(make_case(), store, generator)
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            post = await client.post(
                f"/api/v1/cases/{CASE_ID}/reports",
                json={"report_type": "detailed", "format": "json"},
            )
            assert post.status_code == 202, post.text
            record = session.reports[0]
            download = await client.get(
                f"/api/v1/reports/{record.report_id}/download"
            )
    finally:
        cleanup_overrides()

    assert download.status_code == 200
    rendered = download.content.decode("utf-8")
    report = deserialize_report(rendered)
    # Data fidelity: JSON carries the payload verbatim (escaping is an
    # HTML-rendering concern only) and the export stays machine-readable.
    assert report["sections"]
    assert report["title"] == XSS_PAYLOAD
    assert "<script>alert" in rendered
    assert "&lt;script&gt;" not in rendered


# ----------------------------------------------------------------------
# §8.4 Header-value sanitization on report downloads
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_download_header_is_not_influenced_by_user_controlled_text(tmp_path):
    store = make_store(tmp_path)
    session = store.db
    hostile_title = "Titles \r\nX-Injected: yes"
    generator = fixture_generator()
    generator.grounding = StubGrounding(case={**CASE, "title": hostile_title})
    install_overrides(make_case(), store, generator)
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            post = await client.post(
                f"/api/v1/cases/{CASE_ID}/reports",
                json={"report_type": "detailed", "format": "html"},
            )
            assert post.status_code == 202, post.text
            record = session.reports[0]
            download = await client.get(
                f"/api/v1/reports/{record.report_id}/download"
            )
    finally:
        cleanup_overrides()

    disposition = download.headers["content-disposition"]
    # The filename derives from the server-generated case number only.
    assert disposition == f'attachment; filename="{CASE_NUMBER}_report.html"'
    assert "\r" not in disposition
    assert "\n" not in disposition
    assert "X-Injected" not in str(download.headers)


# ----------------------------------------------------------------------
# Phase 6/7 error scenarios
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_unknown_case_returns_404_error_envelope():
    install_case_db(None)
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/cases/{uuid4()}")
    finally:
        cleanup_overrides()

    assert response.status_code == 404
    error = response.json()["detail"]["error"]
    assert error["code"] == "CASE_NOT_FOUND"
    assert set(error.keys()) == {"code", "message"}


@pytest.mark.asyncio
async def test_risk_summary_without_trace_returns_404_no_trace():
    case = make_case()
    install_case_db(case)
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/cases/{CASE_ID}/risk-summary")
    finally:
        cleanup_overrides()

    assert response.status_code == 404
    assert response.json()["detail"]["error"]["code"] == "NO_TRACE"


@pytest.mark.asyncio
async def test_wallet_risk_with_unknown_trace_id_returns_404():
    case = make_case()
    trace = sample_trace(case)
    install_case_db(case, trace)
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/cases/{CASE_ID}/wallets/{case.reported_wallet_address}/risk",
                params={"trace_id": str(uuid4())},
            )
    finally:
        cleanup_overrides()

    assert response.status_code == 404
    assert response.json()["detail"]["error"]["code"] == "TRACE_NOT_FOUND"


@pytest.mark.asyncio
async def test_unknown_trace_returns_404_error_envelope():
    case = make_case()
    trace = sample_trace(case)
    install_case_db(case, trace)
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/cases/{CASE_ID}/traces/{uuid4()}"
            )
    finally:
        cleanup_overrides()

    assert response.status_code == 404
    error = response.json()["detail"]["error"]
    assert error["code"] in {"TRACE_NOT_FOUND", "NO_TRACE"}
    assert set(error.keys()) == {"code", "message"}


# ----------------------------------------------------------------------
# §8.5 API authentication on every registered route (401 semantics)
# ----------------------------------------------------------------------

PROTECTED_ROUTE_CASE = str(uuid4())
PROTECTED_ROUTE_TRACE = str(uuid4())
PROTECTED_ROUTE_RISK = str(uuid4())
PROTECTED_ROUTE_REPORT = str(uuid4())
PROTECTED_ROUTE_WALLET = "0x" + "a" * 40


def _protected_routes():
    """Every registered API route except the documented public login route."""
    paths = set()
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api/v1/"):
            continue
        for method in sorted(getattr(route, "methods", []) or []):
            if method in {"HEAD", "OPTIONS"}:
                continue
            paths.add((method, path))
    protected = {
        (method, path) for method, path in paths if path != "/api/v1/auth/login"
    }
    rendered = set()
    for method, path in protected:
        rendered.add(
            (
                method,
                path.replace("{case_id}", PROTECTED_ROUTE_CASE)
                .replace("{trace_id}", PROTECTED_ROUTE_TRACE)
                .replace("{risk_id}", PROTECTED_ROUTE_RISK)
                .replace("{report_id}", PROTECTED_ROUTE_REPORT)
                .replace("{wallet_address}", PROTECTED_ROUTE_WALLET),
            )
        )
    return sorted(rendered)


@pytest.mark.asyncio
async def test_every_protected_route_rejects_missing_token():
    routes = _protected_routes()
    # The sweep is only meaningful if it really covers the registered surface.
    # 22 = 18 Phase 1-6 routes + 3 MVP findings routes + 1 Phase 7 auth logout route.
    assert len(routes) == 22, routes

    app.dependency_overrides.pop(get_current_principal, None)
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            for method, path in routes:
                response = await client.request(method, path, json={})
                assert response.status_code == 401, (method, path, response.status_code)
                assert response.json()["detail"]["error"]["code"] == (
                    "AUTHENTICATION_REQUIRED"
                ), (method, path, response.text)
    finally:
        app.dependency_overrides[get_current_principal] = lambda: TEST_PRINCIPAL


@pytest.mark.asyncio
async def test_login_route_stays_public_and_never_leaks_a_token_on_failure():
    install_case_db(None)
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"username": "nobody@agency.gov", "password": "wrong-password"},
            )
    finally:
        cleanup_overrides()

    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "INVALID_CREDENTIALS"
    assert "access_token" not in response.text
