import { useState, useEffect } from "react";
import { Sun, Moon } from "lucide-react";
import "./App.css";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "")
  .replace(/\/+$/, "");

const PIPELINE_STEPS = [
  { label: "Analyze", verb: "Analyzing", meta: "analyze", desc: "Understand the user's goal." },
  { label: "Plan", verb: "Planning", meta: "plan", desc: "Create the best content strategy." },
  { label: "Create", verb: "Creating", meta: "create", desc: "Generate the required content." },
  { label: "Review", verb: "Reviewing", meta: "review", desc: "Check and improve the output." },
];

const AGENTS = [
  {
    num: "01",
    title: "Analyze Agent",
    loadingLabel: "Analyzing your idea",
    meta: "analyze",
    field: "analysis",
    fallback: "No analysis was returned by the AI.",
  },
  {
    num: "02",
    title: "Planning Agent",
    loadingLabel: "Building the content plan",
    meta: "plan",
    field: "plan",
    fallback: "No plan was returned by the AI.",
  },
  {
    num: "03",
    title: "Creation Agent",
    loadingLabel: "Generating content",
    meta: "create",
    field: "content",
    fallback: "No content was created by the AI.",
  },
  {
    num: "04",
    title: "Review Agent",
    loadingLabel: "Reviewing the content",
    meta: "review",
    field: "review",
    fallback: "No review was returned by the AI.",
  },
];

const IDLE_STEPS = {
  analyze: "idle",
  plan: "idle",
  create: "idle",
  review: "idle",
};

function Spinner() {
  return <span className="spinner" aria-hidden="true" />;
}

function App() {
  const [idea, setIdea] = useState("");
  const [status, setStatus] = useState("Ready");
  const [loading, setLoading] = useState(false);
  const [steps, setSteps] = useState(IDLE_STEPS);
  const [data, setData] = useState(null);
  const [copied, setCopied] = useState(null);
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("theme") || "dark";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  const setStep = (meta, state) => {
    setSteps((prev) => ({ ...prev, [meta]: state }));
  };

  const copyText = async (key, text) => {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
    setCopied(key);
    setTimeout(() => setCopied(null), 2000);
  };

  const downloadText = (text, filename) => {
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const downloadFullReport = () => {
    if (!data) return;
    downloadText(
      `═══════════════════════════════════════════════\n` +
        `  AUTONOMOUS AI CREATOR — FULL REPORT\n` +
        `═══════════════════════════════════════════════\n\n` +
        `Generated: ${new Date().toLocaleString()}\n\n` +
        `─ YOUR IDEA ──────────────────────────────────\n\n${data.idea || ""}\n\n` +
        `─ 01 ANALYZE AGENT ──────────────────────────────\n\n${data.analysis || "No analysis was returned."}\n\n` +
        `─ 02 PLANNING AGENT ─────────────────────────────\n\n${data.plan || "No plan was returned."}\n\n` +
        `─ 03 CREATION AGENT ─────────────────────────────\n\n${data.content || "No content was created."}\n\n` +
        `─ 04 REVIEW AGENT ───────────────────────────────\n\n` +
        `${formatReviewForDownload(data.review)}\n\n` +
        `─ FINAL OUTPUT ──────────────────────────────────\n\n${
          data.final_content || data.content || "No final content."
        }\n\n` +
        `═══════════════════════════════════════════════\n` +
        `  END OF REPORT\n` +
        `═══════════════════════════════════════════════\n`,
      "ai-full-report.txt"
    );
  };

  const formatReviewForDownload = (review) => {
    if (!review) return "No review was returned.";
    if (typeof review === "string") return review;
    const parts = [];
    if (review.quality_score != null) {
      parts.push(`QUALITY SCORE: ${review.quality_score}/10`);
    }
    if (review.issues_found?.length) {
      parts.push("ISSUES FOUND:\n" + review.issues_found.map((i) => `- ${i}`).join("\n"));
    }
    if (review.improvements_made?.length) {
      parts.push("IMPROVEMENTS MADE:\n" + review.improvements_made.map((i) => `- ${i}`).join("\n"));
    }
    if (review.status) {
      parts.push(`STATUS: ${review.status}`);
    }
    return parts.join("\n\n");
  };

  const handleStreamEvent = (payload) => {
    const stage = payload.stage;

    switch (stage) {
      case "analyzing":
        setStep("analyze", "loading");
        setStatus(payload.message || "Analyzing your idea...");
        break;

      case "analyzed":
        setData((prev) => ({ ...prev, analysis: payload.analysis || "" }));
        setStep("analyze", "done");
        setStep("plan", "loading");
        setStatus("Planning the content strategy...");
        break;

      case "planned":
        setData((prev) => ({ ...prev, plan: payload.plan || "" }));
        setStep("plan", "done");
        setStep("create", "loading");
        setStatus("Creating the content...");
        break;

      case "creating":
        setStatus(payload.message || "Creating the content...");
        break;

      case "created":
        setData((prev) => ({ ...prev, content: payload.content || "" }));
        setStep("create", "done");
        setStep("review", "loading");
        setStatus("Reviewing the content...");
        break;

      case "reviewed":
        setData((prev) => ({ ...prev, review: payload.review }));
        setStep("review", "done");
        setStatus("Review complete");
        break;

      case "completed":
        setData({
          idea: payload.idea,
          analysis: payload.analysis,
          plan: payload.plan,
          content: payload.content,
          review: payload.review,
          final_content: payload.final_content || payload.content,
        });
        setSteps({
          analyze: "done",
          plan: "done",
          create: "done",
          review: "done",
        });
        setStatus(payload.message || "Content generated successfully.");
        break;

      case "error":
        throw new Error(payload.message || "Generation failed.");
    }
  };

  const runStream = async (body) => {
    const response = await fetch(`${API_BASE}/generate-stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok || !response.body) {
      throw new Error(`Stream failed (${response.status})`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let completed = false;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const events = buffer.split("\n\n");
      buffer = events.pop() || "";

      for (const event of events) {
        const line = event.trim();
        if (!line.startsWith("data:")) continue;
        try {
          const payload = JSON.parse(line.slice(5).trim());
          handleStreamEvent(payload);
          if (payload.stage === "completed") completed = true;
        } catch (error) {
          console.error("Bad SSE event:", error);
        }
      }
    }

    return completed;
  };

  const runLegacy = async (body) => {
    const response = await fetch(`${API_BASE}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const json = await response.json();
    if (!json.success) throw new Error(json.message || "Generation failed.");

    setData({
      idea: json.idea,
      analysis: json.analysis,
      plan: json.plan,
      content: json.content,
      review: json.review,
      final_content: json.final_content || json.content,
    });
    setSteps({
      analyze: "done",
      plan: "done",
      create: "done",
      review: "done",
    });
  };

  const generateContent = async () => {
    if (!idea.trim()) {
      setStatus("Please enter an idea first.");
      return;
    }

    setLoading(true);
    setData(null);
    setCopied(null);
    setSteps(IDLE_STEPS);
    setStatus("Starting the autonomous pipeline...");

    const body = { idea: idea.trim() };

    try {
      const streamed = await runStream(body);
      if (!streamed) throw new Error("Stream ended before completion.");
    } catch (error) {
      console.error("Stream error, falling back to /generate:", error);
      try {
        await runLegacy(body);
        setStatus("Content generated successfully.");
      } catch (legacyError) {
        console.error("Legacy error:", legacyError);
        setSteps(IDLE_STEPS);
        setStatus("Backend connection failed.");
      }
    } finally {
      setLoading(false);
    }
  };

  const stageName = PIPELINE_STEPS.find((s) => steps[s.meta] === "loading");
  const buttonLabel = stageName
    ? `${stageName.verb}...`
    : "Generate Content →";

  const renderAgentCard = (agent) => {
    const state = steps[agent.meta];
    const value = data ? data[agent.field] : null;

    if (state === "idle" && !loading) {
      return (
        <div className="agent-output" key={agent.meta}>
          <div className="agent-title">
            <span>{agent.num}</span>
            <strong>{agent.title}</strong>
          </div>
          <div className="agent-content muted">Waiting for input…</div>
        </div>
      );
    }

    if (state === "loading" && value === null) {
      return (
        <div className="agent-output is-loading" key={agent.meta}>
          <div className="agent-title">
            <span>{agent.num}</span>
            <strong>{agent.title}</strong>
          </div>
          <div className="agent-loading">
            <Spinner />
            <span>{agent.loadingLabel}...</span>
          </div>
        </div>
      );
    }

    return (
      <div className="agent-output is-done" key={agent.meta}>
        <div className="agent-title">
          <span>{agent.num}</span>
          <strong>{agent.title}</strong>
          {state === "done" && <span className="done-tag">✓</span>}
          {agent.field === "content" && value && (
            <button
              className="copy-btn"
              onClick={() => copyText("content", value)}
            >
              {copied === "content" ? "✓ Copied" : "Copy"}
            </button>
          )}
        </div>
        {agent.field === "review" ? (
          <ReviewOutput review={value} />
        ) : (
          <div className="agent-content">
            {value || agent.fallback}
          </div>
        )}
      </div>
    );
  };

  const hasReview = (() => {
    if (!data || !data.review) return false;
    if (typeof data.review === "string") return true;
    return Boolean(
      data.review.quality_score != null ||
        (data.review.issues_found && data.review.issues_found.length) ||
        (data.review.improvements_made && data.review.improvements_made.length) ||
        data.review.status
    );
  })();

  const finalText = data
    ? data.final_content || data.content || ""
    : "";

  return (
    <div className="app">

      {/* HEADER */}
      <header className="navbar">
        <div className="brand">
          <span className="brand-icon">✦</span>
          <span>Autonomous AI Creator</span>
        </div>

        <div className="nav-status">
          <span className="status-dot"></span>
          System Online
        </div>

        <button
          className="theme-toggle"
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
        >
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </header>

      <main className="main-content">

        {/* HERO SECTION */}
        <section className="hero">
          <p className="eyebrow">AI-POWERED CONTENT CREATION</p>

          <h1>
            Turn Your Idea Into
            <br />
            <span>Content Automatically</span>
          </h1>

          <p className="subtitle">
            Give the AI a goal. The autonomous creator analyzes, plans,
            creates, and reviews your content.
          </p>
        </section>

        {/* CREATOR CARD */}
        <section className="creator-card">
          <div className="card-header">
            <div>
              <h2>Start a Creation Task</h2>
              <p>Describe what you want the AI to create.</p>
            </div>

            <div className="agent-badge">
              <span>●</span> AI Agent
            </div>
          </div>

          <textarea
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            placeholder="Example: Create a 7-day Instagram content plan about artificial intelligence..."
            disabled={loading}
          />

          <div className="actions">
            <span className={`status ${loading ? "status-active" : ""}`}>
              {loading && <Spinner />} {status}
            </span>

            <button onClick={generateContent} disabled={loading}>
              {loading ? buttonLabel : "Generate Content →"}
            </button>
          </div>
        </section>

        {/* RESULT SECTION */}
        {(loading || data) && (
          <section className="result-card">
            <div className="result-header">
              <div>
                <p className="result-label">AI CONTENT GENERATED</p>
                <h2>
                  {data ? "Content generated successfully" : "Working on your content"}
                </h2>
              </div>

              <span className={data ? "success-badge" : "success-badge working"}>
                {data ? "✓ Success" : "AI Working"}
              </span>

              {data && (
                <div className="download-buttons">
                  <button
                    className="download-btn download-btn-outline"
                    onClick={downloadFullReport}
                    title="Download full report with all agent outputs"
                  >
                    ⬇ Full Report
                  </button>
                </div>
              )}
            </div>

            {data && data.idea && (
              <div className="idea-result">
                <strong>Your idea</strong>
                <p>{data.idea}</p>
              </div>
            )}

            {AGENTS.map(renderAgentCard)}

            {/* ============================= */}
            {/* FINAL OUTPUT */}
            {/* ============================= */}
            {(steps.create === "done" || data) && (
              <div className="final-output">
                <div className="final-output-header">
                  <div>
                    <span className="result-label">FINAL OUTPUT</span>
                    <h3>Reviewed Content</h3>
                  </div>

                  {hasReview && !loading && (
                    <span className={`approval approved ${String(data?.review?.status || "").toLowerCase().includes("approv") ? "" : "needs-work"}`}>
                      {String(data?.review?.status || "No approval").toUpperCase()}
                    </span>
                  )}

                  <div className="final-actions">
                    <button
                      className="copy-btn"
                      onClick={() => copyText("final", finalText)}
                      disabled={!finalText || loading}
                    >
                      {copied === "final" ? "✓ Copied" : "Copy Content"}
                    </button>
                    <button
                      className="download-btn download-btn-outline"
                      onClick={() => downloadText(finalText || "No content.", "ai-content.txt")}
                      disabled={!finalText || loading}
                      title="Download only the generated content"
                    >
                      ⬇ Content Only
                    </button>
                  </div>
                </div>

                {steps.review === "loading" && !data?.final_content ? (
                  <div className="agent-loading">
                    <Spinner />
                    <span>Waiting for the reviewed content…</span>
                  </div>
                ) : (
                  <div className="content-output final-content">
                    {finalText || "The reviewed content will appear here."}
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        {/* AUTONOMOUS PIPELINE */}
        <section className="pipeline">
          <h2>Autonomous Creation Pipeline</h2>

          <div className="steps">
            {PIPELINE_STEPS.map((step, index) => (
              <div
                className={`step ${steps[step.meta]}`}
                key={step.meta}
              >
                <div className="step-number">
                  {steps[step.meta] === "done" ? (
                    <span className="done-icon">✓</span>
                  ) : steps[step.meta] === "loading" ? (
                    <Spinner />
                  ) : (
                    index + 1
                  )}
                </div>
                <h3>{step.label}</h3>
                <p>{steps[step.meta] === "loading" ? "Working..." : step.desc}</p>
              </div>
            ))}
          </div>
        </section>

      </main>
    </div>
  );
}

// ============================================================
// HELPER COMPONENTS
// ============================================================

function ReviewOutput({ review }) {
  if (!review) {
    return <div className="agent-content muted">No review was returned by the AI.</div>;
  }

  if (typeof review === "string") {
    return <div className="agent-content">{review}</div>;
  }

  const score = review.quality_score;
  const issues = review.issues_found || [];
  const improvements = review.improvements_made || [];
  const status = review.status || "No approval status";

  const scoreClass =
    score == null
      ? "score-none"
      : score >= 8
      ? "score-good"
      : score >= 5
      ? "score-mid"
      : "score-bad";

  return (
    <div className="review-grid">
      <div className={`review-score ${scoreClass}`}>
        <div className="score-main">
          <span className="score-num">{score ?? "–"}</span>
          <span className="score-slash">/10</span>
        </div>
        <span className="score-caption">Quality Score</span>
      </div>

      <div className="review-block">
        <h4>Issues Found</h4>
        {issues.length ? (
          <ul className="review-list">
            {issues.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        ) : (
          <p className="muted">None noted.</p>
        )}
      </div>

      <div className="review-block">
        <h4>Improvements Made</h4>
        {improvements.length ? (
          <ul className="review-list">
            {improvements.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        ) : (
          <p className="muted">None noted.</p>
        )}
      </div>

      <div className="review-approval">
        <span
          className={`approval-dot ${String(status).toLowerCase().includes("approv") ? "approved" : "rejected"}`}
        />
        <strong>Approval:</strong>
        <span className="approval-status">{status}</span>
      </div>
    </div>
  );
}

export default App;