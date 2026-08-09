import os
import sys
import tempfile
from pathlib import Path

import pytest

# Test environment must be configured before `main` / `auth` are imported,
# because they read these at import time.
os.environ["DATABASE_PATH"] = os.path.join(
    tempfile.mkdtemp(prefix="aac-tests-"), "test.db"
)
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ["JWT_EXPIRE_MINUTES"] = "60"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def clean_users():
    """Reset the users table before and after every test so tests are
    isolated and never touch a real users.db."""
    import auth

    with auth.get_connection() as conn:
        conn.execute("DELETE FROM users")
    yield
    with auth.get_connection() as conn:
        conn.execute("DELETE FROM users")


@pytest.fixture
def auth_headers():
    """Register a fresh test user and return authenticated headers.

    The rate limiter is reset afterwards so consuming one request slot
    during registration does not skew rate-limit tests.
    """
    from fastapi.testclient import TestClient

    import main

    client = TestClient(main.app)
    resp = client.post(
        "/auth/register",
        json={"email": "tester@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    main.rate_limiter.reset()
    return {"Authorization": f"Bearer {token}"}
