import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import main
from main import (
    AnalysisModel,
    PlanModel,
    ReviewModel,
    AnalyzePlanOutput,
    CreateReviewOutput,
    InvalidStructuredOutputError,
    format_analysis,
    format_plan,
    review_to_legacy,
    parse_schema_json,
    generate_structured,
    run_pipeline,
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


def _fake_client(text):
    def generate_content(*, model, contents, config):
        return SimpleNamespace(text=text)

    return SimpleNamespace(
        models=SimpleNamespace(generate_content=generate_content)
    )


def _fake_client_with_errors(errors, success_text):
    calls = {"n": 0}

    def generate_content(*, model, contents, config):
        calls["n"] += 1
        if errors:
            raise errors.pop(0)
        return SimpleNamespace(text=success_text)

    return SimpleNamespace(
        models=SimpleNamespace(generate_content=generate_content)
    ), calls


class TestStructuredParsing:
    def test_analyze_plan_output_json(self):
        result = AnalyzePlanOutput.model_validate_json(
            json.dumps(SAMPLE_ANALYZE_PLAN)
        )
        assert result.analysis.summary == "A weekly AI series"
        assert result.analysis.goals == ["Educate", "Grow the channel"]
        assert result.analysis.key_points == ["Keep it simple", "Use examples"]
        assert result.plan.title == "AI Explained"
        assert result.plan.outline == ["Intro", "Core idea", "Examples"]
        assert result.plan.tone == "Friendly"

    def test_create_review_output_json(self):
        result = CreateReviewOutput.model_validate_json(
            json.dumps(SAMPLE_CREATE_REVIEW)
        )
        assert result.content == "Draft content body"
        assert result.final_content == "Improved content body"
        assert result.review.score == 9
        assert result.review.issues == ["Add a stronger hook"]
        assert result.review.improvements == ["Hook rewritten"]
        assert result.review.approved is True

    def test_parse_schema_json_strips_fences(self):
        fenced = "```json\n" + json.dumps(SAMPLE_ANALYZE_PLAN) + "\n```"
        result = parse_schema_json(AnalyzePlanOutput, fenced)
        assert result.plan.title == "AI Explained"

    def test_parse_schema_json_rejects_invalid(self):
        with pytest.raises(Exception):
            parse_schema_json(AnalyzePlanOutput, "{ not valid json")


class TestFormatting:
    def test_format_analysis(self):
        analysis = AnalysisModel(**SAMPLE_ANALYZE_PLAN["analysis"])
        out = format_analysis(analysis)
        assert "A weekly AI series" in out
        assert "Target audience: Beginners" in out
        assert "Content type: Series" in out
        assert "Goals:" in out
        assert "- Educate" in out
        assert "Key points:" in out
        assert "- Keep it simple" in out

    def test_format_plan(self):
        plan = PlanModel(**SAMPLE_ANALYZE_PLAN["plan"])
        out = format_plan(plan)
        assert "Title: AI Explained" in out
        assert "Hook: Ever wondered how AI works?" in out
        assert "Tone: Friendly" in out
        assert "Strategy: Publish weekly, short episodes" in out
        assert "Outline:" in out
        assert "- Intro" in out

    def test_review_to_legacy_maps_frontend_fields(self):
        review = ReviewModel(**SAMPLE_CREATE_REVIEW["review"])
        legacy = review_to_legacy(review)
        assert legacy["quality_score"] == 9
        assert legacy["issues_found"] == ["Add a stronger hook"]
        assert legacy["improvements_made"] == ["Hook rewritten"]
        assert legacy["status"] == "Approved"
        assert legacy["strengths"] == []

    def test_review_to_legacy_needs_work(self):
        review = ReviewModel(
            score=4, issues=["x"], improvements=[], approved=False
        )
        legacy = review_to_legacy(review)
        assert legacy["quality_score"] == 4
        assert legacy["status"] == "Needs Work"


class TestGenerateStructured:
    def test_valid_output(self, monkeypatch):
        monkeypatch.setattr(
            main, "client",
            _fake_client(json.dumps(SAMPLE_ANALYZE_PLAN))
        )
        result = generate_structured("prompt", AnalyzePlanOutput, "Analyze")
        assert isinstance(result, AnalyzePlanOutput)
        assert result.analysis.audience == "Beginners"

    def test_invalid_output_raises_clear_error(self, monkeypatch):
        monkeypatch.setattr(
            main, "time", SimpleNamespace(sleep=lambda s: None)
        )
        monkeypatch.setattr(
            main, "client", _fake_client("{ not valid json")
        )
        with pytest.raises(InvalidStructuredOutputError):
            generate_structured("prompt", AnalyzePlanOutput, "Analyze")

    def test_transient_error_is_retried(self, monkeypatch):
        monkeypatch.setattr(
            main, "time", SimpleNamespace(sleep=lambda s: None)
        )
        fake, calls = _fake_client_with_errors(
            [RuntimeError("429 Too Many Requests")],
            json.dumps(SAMPLE_ANALYZE_PLAN),
        )
        monkeypatch.setattr(main, "client", fake)
        result = generate_structured("prompt", AnalyzePlanOutput, "Analyze")
        assert calls["n"] == 2
        assert isinstance(result, AnalyzePlanOutput)

    def test_permanent_error_is_not_retried(self, monkeypatch):
        monkeypatch.setattr(
            main, "time", SimpleNamespace(sleep=lambda s: None)
        )
        fake, calls = _fake_client_with_errors(
            [RuntimeError("401 Unauthorized")],
            json.dumps(SAMPLE_ANALYZE_PLAN),
        )
        monkeypatch.setattr(main, "client", fake)
        with pytest.raises(RuntimeError):
            generate_structured("prompt", AnalyzePlanOutput, "Analyze")
        assert calls["n"] == 1


class TestRunPipeline:
    def test_emits_stages_and_returns_payload(self, monkeypatch):
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

        events = []
        result = run_pipeline("my idea", emit=events.append)

        stages = [e["stage"] for e in events]
        assert stages == [
            "analyzing", "analyzed", "planned",
            "creating", "created", "reviewed",
        ]
        assert "Target audience: Beginners" in events[1]["analysis"]
        assert "Title: AI Explained" in events[2]["plan"]
        assert events[3]["stage"] == "creating"
        assert events[4]["content"] == "Draft content body"
        assert events[5]["review"]["quality_score"] == 9

        assert result["idea"] == "my idea"
        assert result["analysis"] == events[1]["analysis"]
        assert result["plan"] == events[2]["plan"]
        assert result["content"] == "Draft content body"
        assert result["final_content"] == "Improved content body"
        assert result["review"]["status"] == "Approved"
        assert result["pipeline"] == ["Analyze", "Plan", "Create", "Review"]


class TestEndpoints:
    @pytest.fixture(autouse=True)
    def reset_rate_limiter(self):
        main.rate_limiter.reset()
        yield

    @pytest.fixture
    def client(self, monkeypatch, auth_headers):
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

    def _read_sse_stages(self, body):
        events = []
        for line in body.splitlines():
            line = line.strip()
            if line.startswith("data: "):
                events.append(json.loads(line[len("data: "):]))
        return events

    def test_generate_stream_emits_all_stages(self, client):
        with client.stream(
            "POST", "/generate-stream", json={"idea": "test idea"}
        ) as resp:
            body = resp.read().decode()

        events = self._read_sse_stages(body)
        stages = [e["stage"] for e in events]
        assert stages == [
            "analyzing", "analyzed", "planned",
            "creating", "created", "reviewed", "completed",
        ]
        assert "Target audience: Beginners" in events[1]["analysis"]
        assert events[2]["plan"]
        assert events[4]["content"] == "Draft content body"
        assert events[5]["review"]["quality_score"] == 9

        last = events[-1]
        assert last["final_content"] == "Improved content body"
        assert last["content"] == "Draft content body"
        assert last["idea"] == "test idea"
        assert last["pipeline"] == ["Analyze", "Plan", "Create", "Review"]

    def test_generate_returns_payload(self, client):
        resp = client.post("/generate", json={"idea": "test idea"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["analysis"]
        assert data["plan"]
        assert data["content"] == "Draft content body"
        assert data["final_content"] == "Improved content body"
        assert data["review"]["quality_score"] == 9
        assert data["review"]["status"] == "Approved"

    def test_generate_empty_idea(self, client):
        resp = client.post("/generate", json={"idea": "   "})
        assert resp.status_code == 422
        data = resp.json()
        assert data["success"] is False
        assert "idea" in data["message"].lower()

    def test_generate_stream_empty_idea(self, client):
        resp = client.post("/generate-stream", json={"idea": "   "})
        assert resp.status_code == 422
        data = resp.json()
        assert data["success"] is False
        assert "idea" in data["message"].lower()
