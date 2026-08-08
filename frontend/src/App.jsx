import { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [idea, setIdea] = useState("");
  const [status, setStatus] = useState("Ready");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const generateContent = async () => {
    if (!idea.trim()) {
      setStatus("Please enter an idea first.");
      return;
    }

    setLoading(true);
    setResult(null);
    setStatus("AI is analyzing your idea...");

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/generate",
        {
          idea: idea.trim(),
        }
      );

      if (response.data.success) {
        setStatus("Content generated successfully.");
        setResult(response.data);
      } else {
        setStatus(response.data.message || "Generation failed.");
      }
    } catch (error) {
      console.error("Generation error:", error);
      setStatus("Backend connection failed.");
    } finally {
      setLoading(false);
    }
  };

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
          />

          <div className="actions">
            <span className="status">{status}</span>

            <button
              onClick={generateContent}
              disabled={loading}
            >
              {loading ? "Processing..." : "Generate Content →"}
            </button>
          </div>

        </section>

        {/* RESULT SECTION */}
        {result && (
          <section className="result-card">

            {/* RESULT HEADER */}
            <div className="result-header">
              <div>
                <p className="result-label">
                  AI CONTENT GENERATED
                </p>

                <h2>
                  Content generated successfully
                </h2>
              </div>

              <span className="success-badge">
                ✓ Success
              </span>
            </div>

            {/* USER IDEA */}
            <div className="idea-result">
              <strong>Your idea</strong>
              <p>{result.idea}</p>
            </div>

            {/* ============================= */}
            {/* 01 ANALYZE AGENT */}
            {/* ============================= */}

            <div className="agent-output">

              <div className="agent-title">
                <span>01</span>
                <strong>Analyze Agent</strong>
              </div>

              <div className="agent-content">
                {result.analysis ||
                  "No analysis was returned by the AI."}
              </div>

            </div>

            {/* ============================= */}
            {/* 02 PLANNING AGENT */}
            {/* ============================= */}

            <div className="agent-output">

              <div className="agent-title">
                <span>02</span>
                <strong>Planning Agent</strong>
              </div>

              <div className="agent-content">
                {result.plan ||
                  "No plan was returned by the AI."}
              </div>

            </div>

            {/* ============================= */}
            {/* 03 CREATION AGENT */}
            {/* ============================= */}

            <div className="agent-output">

              <div className="agent-title">
                <span>03</span>
                <strong>Creation Agent</strong>
              </div>

              <div className="agent-content">
                {result.content ||
                  "No content was created by the AI."}
              </div>

            </div>

            {/* ============================= */}
            {/* 04 REVIEW AGENT */}
            {/* ============================= */}

            <div className="agent-output">

              <div className="agent-title">
                <span>04</span>
                <strong>Review Agent</strong>
              </div>

              <div className="agent-content">
                {result.review ||
                  "No review was returned by the AI."}
              </div>

            </div>

          </section>
        )}

        {/* AUTONOMOUS PIPELINE */}
        <section className="pipeline">

          <h2>Autonomous Creation Pipeline</h2>

          <div className="steps">

            {/* ANALYZE */}
            <div className="step">
              <div className="step-number">1</div>
              <h3>Analyze</h3>
              <p>Understand the user's goal.</p>
            </div>

            <div className="line"></div>

            {/* PLAN */}
            <div className="step">
              <div className="step-number">2</div>
              <h3>Plan</h3>
              <p>Create the best content strategy.</p>
            </div>

            <div className="line"></div>

            {/* CREATE */}
            <div className="step">
              <div className="step-number">3</div>
              <h3>Create</h3>
              <p>Generate the required content.</p>
            </div>

            <div className="line"></div>

            {/* REVIEW */}
            <div className="step">
              <div className="step-number">4</div>
              <h3>Review</h3>
              <p>Check and improve the output.</p>
            </div>

          </div>

        </section>

      </main>
    </div>
  );
}

export default App;