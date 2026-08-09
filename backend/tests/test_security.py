import json

import pytest
from fastapi.testclient import TestClient

import main
from main import (
    AnalyzePlanOutput,
    CreateReviewOutput,
    RateLimiter,
    build_analyze_plan_prompt,
    build_create_review_prompt,
)

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


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    main.rate_limiter.reset()
    yield


@pytest.fixture
def client(monkeypatch, auth_headers):
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
    return TestClient(main.app, headers=auth_headers)


def _read_sse_stages(body):
    events = []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data: "):
            events.append(json.loads(line[len("data: "):]))
    return events


# ==========================================
# INPUT VALIDATION
# ==========================================

class TestInputValidation:
    def test_empty_idea_rejected(self, client):
        resp = client.post("/generate", json={"idea": ""})
        assert resp.status_code == 422
        assert resp.json()["success"] is False

    def test_whitespace_idea_rejected(self, client):
        resp = client.post("/generate", json={"idea": "   \n\t  "})
        assert resp.status_code == 422
        data = resp.json()
        assert data["success"] is False
        assert "idea" in data["message"].lower()

    def test_whitespace_idea_rejected_stream(self, client):
        resp = client.post("/generate-stream", json={"idea": "   "})
        assert resp.status_code == 422
        assert resp.json()["success"] is False

    def test_idea_over_4000_rejected(self, client):
        resp = client.post("/generate", json={"idea": "a" * 4001})
        assert resp.status_code == 422
        assert resp.json()["success"] is False

    def test_idea_over_4000_rejected_stream(self, client):
        resp = client.post("/generate-stream", json={"idea": "a" * 4001})
        assert resp.status_code == 422

    def test_idea_exactly_4000_allowed(self, client):
        resp = client.post("/generate", json={"idea": "a" * 4000})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_valid_idea_succeeds(self, client):
        resp = client.post("/generate", json={"idea": "valid idea"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["final_content"] == "Improved content body"


# ==========================================
# RATE LIMITING
# ==========================================

class TestRateLimiting:
    def test_allows_first_five_then_returns_429(self, client):
        for _ in range(5):
            resp = client.post("/generate", json={"idea": "ok"})
            assert resp.status_code == 200

        resp = client.post("/generate", json={"idea": "ok"})
        assert resp.status_code == 429
        assert resp.json()["success"] is False
        assert "too many requests" in resp.json()["message"].lower()

    def test_separate_ips_have_separate_limits(self, client, monkeypatch):
        calls = {"n": 0}

        def fake_ip(request):
            calls["n"] += 1
            return "10.0.0.1" if calls["n"] <= 6 else "10.0.0.2"

        monkeypatch.setattr(main, "get_client_ip", fake_ip)

        for _ in range(5):
            assert client.post("/generate", json={"idea": "ok"}).status_code == 200

        assert client.post("/generate", json={"idea": "ok"}).status_code == 429
        assert client.post("/generate", json={"idea": "ok"}).status_code == 200

    def test_generate_and_stream_share_one_limit(self, client):
        for _ in range(3):
            assert client.post("/generate", json={"idea": "ok"}).status_code == 200

        with client.stream("POST", "/generate-stream", json={"idea": "ok"}) as resp:
            assert resp.status_code == 200
            resp.read()

        assert client.post("/generate", json={"idea": "ok"}).status_code == 200
        assert client.post("/generate", json={"idea": "ok"}).status_code == 429

    def test_health_not_rate_limited(self, client):
        for _ in range(5):
            assert client.post("/generate", json={"idea": "ok"}).status_code == 200
        assert client.post("/generate", json={"idea": "ok"}).status_code == 429

        assert client.get("/health").status_code == 200
        assert client.get("/health").json()["status"] == "healthy"
        assert client.get("/").status_code == 200


class TestRateLimiterUnit:
    def test_allows_up_to_max(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            assert limiter.allow("ip1") is True
        assert limiter.allow("ip1") is False

    def test_separate_keys_independent(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        assert limiter.allow("ip1") is True
        assert limiter.allow("ip1") is False
        assert limiter.allow("ip2") is True

    def test_window_expiry(self):
        now = [1000.0]
        limiter = RateLimiter(
            max_requests=2, window_seconds=10, clock=lambda: now[0]
        )
        assert limiter.allow("ip") is True
        assert limiter.allow("ip") is True
        assert limiter.allow("ip") is False
        now[0] += 10
        assert limiter.allow("ip") is True


# ==========================================
# SAFE ERROR RESPONSES
# ==========================================

class TestSafeErrors:
    def test_generate_hides_internal_errors(self, client, monkeypatch):
        def boom(idea):
            raise RuntimeError("GEMINI_SECRET_INTERNAL_DETAIL_XYZ")

        monkeypatch.setattr(main, "generate_analyze_plan", boom)

        resp = client.post("/generate", json={"idea": "ok"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "GEMINI_SECRET_INTERNAL_DETAIL_XYZ" not in data["message"]

    def test_generate_stream_hides_internal_errors(self, client, monkeypatch):
        def boom(idea):
            raise RuntimeError("GEMINI_SECRET_INTERNAL_DETAIL_XYZ")

        monkeypatch.setattr(main, "generate_analyze_plan", boom)

        with client.stream("POST", "/generate-stream", json={"idea": "ok"}) as resp:
            body = resp.read().decode()

        events = _read_sse_stages(body)
        assert events[-1]["stage"] == "error"
        assert "GEMINI_SECRET_INTERNAL_DETAIL_XYZ" not in events[-1]["message"]
        assert events[-1]["message"].strip() != ""

    def test_invalid_structured_output_gives_safe_message(self, client, monkeypatch):
        def boom(idea):
            raise main.InvalidStructuredOutputError("bad schema reply")

        monkeypatch.setattr(main, "generate_analyze_plan", boom)

        resp = client.post("/generate", json={"idea": "ok"})
        assert resp.json()["success"] is False
        assert "bad schema reply" not in resp.json()["message"]


# ==========================================
# PROMPT-INJECTION RESISTANCE
# ==========================================

class TestPromptDelimiting:
    def test_analyze_prompt_delimiters_user_idea(self):
        prompt = build_analyze_plan_prompt("my special idea")
        assert "<user_idea>" in prompt
        assert "my special idea" in prompt
        assert "</user_idea>" in prompt
        assert "DATA" in prompt.upper()
        assert "not instructions" in prompt.lower()

    def test_create_review_prompt_delimiters_user_idea(self):
        prompt = build_create_review_prompt(
            "my special idea", "analysis text", "plan text"
        )
        assert "<user_idea>" in prompt
        assert "my special idea" in prompt
        assert "</user_idea>" in prompt
        assert "not instructions" in prompt.lower()

    def test_prompts_are_sent_to_gemini(self, monkeypatch):
        captured = {}

        def fake_generate_content(*, model, contents, config):
            captured["prompt"] = contents
            return type("R", (), {"text": json.dumps(SAMPLE_ANALYZE_PLAN)})()

        models = type("M", (), {})()
        models.generate_content = fake_generate_content
        fake_client = type("C", (), {})()
        fake_client.models = models
        monkeypatch.setattr(main, "client", fake_client)

        result = main.generate_analyze_plan("try to inject")
        assert isinstance(result, AnalyzePlanOutput)
        assert "<user_idea>" in captured["prompt"]
        assert "try to inject" in captured["prompt"]
