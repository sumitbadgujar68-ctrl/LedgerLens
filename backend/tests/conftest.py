"""Phase 7 shared test fixtures.

The application now enforces JWT authentication (SEC-01) and case ownership
authorization (SEC-02). Every pre-existing Phase 1-6 test exercises route
logic as the single investigator that previously owned all fixture data, so
this file overrides only the principal dependency. Authentication and
authorization behaviour itself is asserted in tests/test_security_auth.py,
which removes this override.
"""

import pytest

from app.api.v1.cases import MOCK_INVESTIGATOR_ID
from app.main import app
from app.services.auth.deps import Principal, get_current_principal

TEST_PRINCIPAL = Principal(
    investigator_id=MOCK_INVESTIGATOR_ID,
    username="investigator@test.local",
    full_name="Test Investigator",
    role="investigator",
)


@pytest.fixture(autouse=True)
def authenticated_principal() -> Principal:
    app.dependency_overrides[get_current_principal] = lambda: TEST_PRINCIPAL
    yield TEST_PRINCIPAL
    app.dependency_overrides.pop(get_current_principal, None)
