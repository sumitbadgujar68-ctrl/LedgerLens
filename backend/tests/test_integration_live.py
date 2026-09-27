"""Phase 18 — real integration tests for the paths the MVP verifies.

Unlike the unit suites, these tests exercise the ACTUAL dependency path: no
``app.dependency_overrides`` entries are installed for ``get_db``,
``get_copilot_engine``, ``get_report_store``, ``get_report_generator`` or
``get_current_principal``. Authentication uses a real JWT issued by
POST /auth/login against the real database.

The Copilot checks use a nonexistent case id: FastAPI resolves dependencies
before invoking the handler, so receiving 404 (instead of the historical 422
``{"loc":["query","db"]}``) proves ``get_copilot_engine`` injects its
AsyncSession correctly — without spending an LLM call. The engine is still
constructed for real during dependency resolution.

Skipped automatically when the demo credential or the database is unavailable,
so the offline unit suite stays green.
"""

import asyncio
import os
import tempfile
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.api.v1.reports import get_report_generator
from app.db.database import async_session_maker, engine, get_db
from app.main import app
from app.services.ai.engine import get_copilot_engine
from app.services.auth.deps import get_current_principal
from app.services.reporting import get_report_store

DEMO_USERNAME = os.environ.get("DEMO_INVESTIGATOR_USERNAME", "demo@ledgerlens.local")
PASSWORD_ENV = "INVESTIGATOR_PASSWORD"
PASSWORD_FILE = Path(tempfile.gettempdir()) / "ll_demo_pw.txt"
MISSING_CASE_ID = "00000000-0000-0000-0000-000000000000"

# Anything overridden here would mean the test is no longer exercising the
# real dependency path.
REAL_PATH_KEYS = (
    get_db,
    get_copilot_engine,
    get_report_store,
    get_report_generator,
    get_current_principal,
)


def _no_overrides() -> None:
    active = [key for key in REAL_PATH_KEYS if key in app.dependency_overrides]
    assert not active, f"dependency overrides active for real integration path: {active}"


def _demo_password() -> str | None:
    password = os.environ.get(PASSWORD_ENV)
    if password:
        return password.strip()
    if PASSWORD_FILE.exists():
        return PASSWORD_FILE.read_text(encoding="utf-8").strip()
    return None


@pytest.fixture(scope="module")
def event_loop():
    """One event loop for the whole module.

    The real async engine pools connections bound to their creating loop; a
    per-test loop would hand loop-A connections to loop-B and fail. The pool
    is disposed here, from the same loop that filled it, before it closes.
    """
    loop = asyncio.new_event_loop()
    yield loop
    try:
        loop.run_until_complete(engine.dispose())
    except Exception:  # noqa: BLE001 - best-effort cleanup
        pass
    loop.close()


@pytest.fixture
async def real_app():
    """Strip every real-path override for the duration of one test."""
    saved = {key: app.dependency_overrides.pop(key, None) for key in REAL_PATH_KEYS}
    _no_overrides()
    yield app
    for key, value in saved.items():
        if value is not None:
            app.dependency_overrides[key] = value


@pytest.fixture
async def auth_headers():
    password = _demo_password()
    if not password:
        pytest.skip("demo credential unavailable (INVESTIGATOR_PASSWORD or temp file missing)")
    try:
        async with async_session_maker() as session:
            await session.execute(text("select 1"))
    except Exception as exc:  # noqa: BLE001 - connectivity probe
        pytest.skip(f"real database unavailable: {type(exc).__name__}: {str(exc)[:160]}")

    async with AsyncClient(app=app, base_url="http://test", timeout=60.0) as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": DEMO_USERNAME, "password": password},
        )
    if response.status_code != 200:
        pytest.skip(f"demo login unavailable (HTTP {response.status_code})")
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def demo_case(auth_headers):
    async with AsyncClient(app=app, base_url="http://test", timeout=60.0) as client:
        response = await client.get("/api/v1/cases", headers=auth_headers)
    assert response.status_code == 200, response.text
    cases = response.json()
    assert cases, "expected seeded demo cases in the real database"
    return cases[0]


@pytest.mark.asyncio
async def test_real_login_issues_jwt_without_overrides(real_app, auth_headers):
    async with AsyncClient(app=app, base_url="http://test", timeout=60.0) as client:
        me = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert me.status_code == 200
    assert me.json()["username"] == DEMO_USERNAME
    _no_overrides()


@pytest.mark.asyncio
async def test_real_copilot_dependency_injection_no_422(real_app, auth_headers):
    """ask/summarize/explain_risk must not 422 on the injected db parameter."""
    async with AsyncClient(app=app, base_url="http://test", timeout=60.0) as client:
        ask = await client.post(
            f"/api/v1/cases/{MISSING_CASE_ID}/copilot/ask",
            json={"question": "hello"},
            headers=auth_headers,
        )
        summarize = await client.post(
            f"/api/v1/cases/{MISSING_CASE_ID}/copilot/summarize",
            json={},
            headers=auth_headers,
        )
        explain = await client.post(
            f"/api/v1/cases/{MISSING_CASE_ID}/copilot/explain_risk",
            json={"wallet_address": "0x" + "1" * 40},
            headers=auth_headers,
        )

    for name, response in (("ask", ask), ("summarize", summarize), ("explain_risk", explain)):
        assert response.status_code != 422, f"{name} regressed to 422: {response.text}"
        assert response.status_code == 404, f"{name}: {response.status_code} {response.text}"
        assert response.json()["detail"]["error"]["code"] == "CASE_NOT_FOUND"
    _no_overrides()


@pytest.mark.asyncio
async def test_real_report_store_dependency_round_trip(real_app, auth_headers, demo_case):
    """POST/GET/download against the real get_report_store and real database."""
    case_id = demo_case["case_id"]
    async with AsyncClient(app=app, base_url="http://test", timeout=120.0) as client:
        created = await client.post(
            f"/api/v1/cases/{case_id}/reports",
            json={"report_type": "summary", "format": "json"},
            headers=auth_headers,
        )
        assert created.status_code == 202, created.text

        listed = await client.get(f"/api/v1/cases/{case_id}/reports", headers=auth_headers)
        assert listed.status_code == 200, listed.text
        reports = listed.json()["reports"]
        assert reports, "expected at least one persisted report"

        downloaded = await client.get(
            f"/api/v1/reports/{reports[0]['report_id']}/download",
            headers=auth_headers,
        )
        assert downloaded.status_code == 200
        assert len(downloaded.content) > 0
    _no_overrides()


@pytest.mark.asyncio
async def test_real_findings_risk_and_graph_endpoints(real_app, auth_headers, demo_case):
    """Patterns/evidence/attributions/risk/trace read from the real database."""
    case_id = demo_case["case_id"]
    wallet = demo_case["reported_wallet_address"]
    async with AsyncClient(app=app, base_url="http://test", timeout=60.0) as client:
        patterns = await client.get(f"/api/v1/cases/{case_id}/patterns", headers=auth_headers)
        evidence = await client.get(f"/api/v1/cases/{case_id}/evidence", headers=auth_headers)
        attributions = await client.get(
            f"/api/v1/cases/{case_id}/attributions", headers=auth_headers
        )
        risk = await client.get(
            f"/api/v1/cases/{case_id}/wallets/{wallet}/risk", headers=auth_headers
        )
        traces = await client.get(f"/api/v1/cases/{case_id}/traces", headers=auth_headers)

        assert patterns.status_code == 200, patterns.text
        assert evidence.status_code == 200, evidence.text
        assert attributions.status_code == 200, attributions.text
        for item in patterns.json()["patterns"]:
            assert isinstance(item["demo_data"], bool)
            assert item["finding_source"] in ("demo", "live_trace_derived")
        for item in evidence.json()["evidence"]:
            assert isinstance(item["demo_data"], bool)
        for item in attributions.json()["attributions"]:
            assert isinstance(item["demo_data"], bool)

        assert risk.status_code == 200, risk.text
        assert "score" in risk.json()

        assert traces.status_code == 200, traces.text
        trace_list = traces.json()
        if trace_list:
            detail = await client.get(
                f"/api/v1/cases/{case_id}/traces/{trace_list[0]['trace_id']}",
                headers=auth_headers,
            )
            assert detail.status_code == 200
            body = detail.json()
            assert body["graph"] is not None, "seeded demo trace must include a graph"
            assert body["graph"]["node_count"] > 0
    _no_overrides()
