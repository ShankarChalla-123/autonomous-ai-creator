import json

import jwt
import pytest
from fastapi.testclient import TestClient

import auth
import main
from main import AnalyzePlanOutput, CreateReviewOutput

SAMPLE_ANALYZE_PLAN = {
    "analysis": {
        "summary": "A weekly AI series",
        "audience": "Beginners",
        "goals": ["Educate", "Grow the channel"],
        "content_type": "Series",
        "key_points": ["Keep it simple", "Use examples"],
    },
    "plan": {
        "title": "AI Explained",
        "hook": "Ever wondered how AI works?",
        "outline": ["Intro", "Core idea", "Examples"],
        "tone": "Friendly",
        "strategy": "Publish weekly, short episodes",
    },
}

SAMPLE_CREATE_REVIEW = {
    "content": "Draft content body",
    "final_content": "Improved content body",
    "review": {
        "score": 9,
        "issues": ["Add a stronger hook"],
        "improvements": ["Hook rewritten"],
        "approved": True,
    },
}

EMAIL = "alice@example.com"
PASSWORD = "supersecret123"


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    main.rate_limiter.reset()
    yield


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def client_with_gemini(monkeypatch):
    def fake_analyze_plan(idea):
        return AnalyzePlanOutput.model_validate_json(
            json.dumps(SAMPLE_ANALYZE_PLAN)
        )

    def fake_create_review(idea, stage1):
        return CreateReviewOutput.model_validate_json(
            json.dumps(SAMPLE_CREATE_REVIEW)
        )

    monkeypatch.setattr(main, "generate_analyze_plan", fake_analyze_plan)
    monkeypatch.setattr(main, "generate_create_review", fake_create_review)
    return TestClient(main.app)


def _register(client, email=EMAIL, password=PASSWORD):
    return client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )


def _register_token(client, email=EMAIL, password=PASSWORD):
    resp = _register(client, email, password)
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ==========================================
# REGISTRATION
# ==========================================

class TestRegistration:
    def test_register_success(self, client):
        resp = _register(client)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["token_type"] == "bearer"
        assert data["access_token"]
        assert data["user"]["email"] == EMAIL
        assert data["user"]["id"] > 0

    def test_duplicate_registration_rejected(self, client):
        assert _register(client).status_code == 200
        resp = _register(client)
        assert resp.status_code == 409
        assert resp.json()["success"] is False
        assert "already exists" in resp.json()["message"].lower()

    def test_duplicate_registration_case_insensitive(self, client):
        assert _register(client).status_code == 200
        resp = _register(client, email=EMAIL.upper())
        assert resp.status_code == 409

    def test_short_password_rejected(self, client):
        resp = _register(client, password="short")
        assert resp.status_code == 422
        assert resp.json()["success"] is False

    def test_invalid_email_rejected(self, client):
        resp = _register(client, email="not-an-email")
        assert resp.status_code == 422
        assert resp.json()["success"] is False


class TestPasswordHashing:
    def test_hashes_are_bcrypt_and_not_plaintext(self):
        hashed = auth.hash_password(PASSWORD)
        assert hashed != PASSWORD
        assert hashed.startswith("$2")
        assert auth.verify_password(PASSWORD, hashed) is True
        assert auth.verify_password("wrong-password", hashed) is False

    def test_hashes_are_unique_per_password(self):
        h1 = auth.hash_password(PASSWORD)
        h2 = auth.hash_password(PASSWORD)
        assert h1 != h2

    def test_stored_password_is_hashed(self, client):
        _register(client)
        user = auth.get_user_by_email(EMAIL)
        assert user is not None
        assert user["password_hash"] != PASSWORD
        assert user["password_hash"].startswith("$2")
        assert auth.verify_password(PASSWORD, user["password_hash"]) is True


# ==========================================
# LOGIN
# ==========================================

class TestLogin:
    def test_login_success(self, client):
        _register(client)
        resp = client.post(
            "/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["access_token"]
        assert data["user"]["email"] == EMAIL

    def test_login_wrong_password(self, client):
        _register(client)
        resp = client.post(
            "/auth/login",
            json={"email": EMAIL, "password": "wrongpass123"},
        )
        assert resp.status_code == 401
        assert resp.json()["success"] is False
        assert "invalid email or password" in resp.json()["message"].lower()

    def test_login_nonexistent_user(self, client):
        resp = client.post(
            "/auth/login",
            json={"email": "ghost@example.com", "password": PASSWORD},
        )
        assert resp.status_code == 401
        assert resp.json()["success"] is False

    def test_login_email_case_insensitive(self, client):
        _register(client)
        resp = client.post(
            "/auth/login",
            json={"email": EMAIL.upper(), "password": PASSWORD},
        )
        assert resp.status_code == 200


# ==========================================
# /auth/me
# ==========================================

class TestAuthMe:
    def test_me_valid_token(self, client):
        token = _register_token(client)
        resp = client.get("/auth/me", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["user"]["email"] == EMAIL
        assert data["user"]["id"] > 0
        assert data["user"]["created_at"]

    def test_me_missing_token(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401
        assert resp.json()["success"] is False

    def test_me_invalid_token(self, client):
        resp = client.get("/auth/me", headers=_auth("not.a.valid.token"))
        assert resp.status_code == 401
        assert resp.json()["success"] is False

    def test_me_token_signed_with_wrong_secret(self, client):
        bad_token = jwt.encode(
            {"sub": EMAIL}, "wrong-secret-key", algorithm="HS256"
        )
        resp = client.get("/auth/me", headers=_auth(bad_token))
        assert resp.status_code == 401

    def test_me_expired_token(self, client):
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        expired = jwt.encode(
            {
                "sub": EMAIL,
                "iat": now - timedelta(hours=2),
                "exp": now - timedelta(hours=1),
            },
            auth.JWT_SECRET_KEY,
            algorithm=auth.JWT_ALGORITHM,
        )
        resp = client.get("/auth/me", headers=_auth(expired))
        assert resp.status_code == 401


# ==========================================
# PROTECTED ENDPOINTS
# ==========================================

class TestProtectedGenerate:
    def test_generate_unauthenticated_401(self, client):
        resp = client.post("/generate", json={"idea": "test idea"})
        assert resp.status_code == 401
        assert resp.json()["success"] is False

    def test_generate_stream_unauthenticated_401(self, client):
        resp = client.post("/generate-stream", json={"idea": "test idea"})
        assert resp.status_code == 401
        assert resp.json()["success"] is False

    def test_generate_unauthenticated_invalid_token_401(self, client):
        resp = client.post(
            "/generate",
            json={"idea": "test idea"},
            headers=_auth("garbage-token"),
        )
        assert resp.status_code == 401

    def test_generate_authenticated(self, client_with_gemini):
        token = _register_token(client_with_gemini)
        resp = client_with_gemini.post(
            "/generate",
            json={"idea": "test idea"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["final_content"] == "Improved content body"

    def test_generate_stream_authenticated(self, client_with_gemini):
        token = _register_token(client_with_gemini)
        with client_with_gemini.stream(
            "POST",
            "/generate-stream",
            json={"idea": "test idea"},
            headers=_auth(token),
        ) as resp:
            body = resp.read().decode()

        stages = []
        for line in body.splitlines():
            line = line.strip()
            if line.startswith("data: "):
                stages.append(json.loads(line[len("data: "):])["stage"])
        assert "completed" in stages
        assert stages[:6] == [
            "analyzing", "analyzed", "planned",
            "creating", "created", "reviewed",
        ]


# ==========================================
# TOKEN HELPER UNIT TESTS
# ==========================================

class TestTokens:
    def test_access_token_round_trip(self):
        token = auth.create_access_token(EMAIL)
        payload = auth.decode_access_token(token)
        assert payload["sub"] == EMAIL
        assert payload["exp"] > payload["iat"]

    def test_token_expires(self):
        from datetime import datetime, timedelta, timezone

        token = auth.create_access_token(EMAIL)
        payload = auth.decode_access_token(token)
        expected = datetime.now(timezone.utc) + timedelta(
            minutes=auth.JWT_EXPIRE_MINUTES
        )
        assert abs(payload["exp"] - int(expected.timestamp())) <= 60
