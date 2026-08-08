# 🤖 Autonomous AI Creator

An AI-powered content creation system that transforms a single idea into structured, publish-ready content using a **multi-agent autonomous pipeline**. Instead of relying on one monolithic prompt, the system orchestrates four specialized AI agents — **Analyze → Plan → Create → Review** — each handling a distinct stage of the content workflow.

Built with a **React + Vite** frontend and a **FastAPI** backend, powered by the **Google Gemini API**.

---

## 🚀 Features

- 💡 **Idea-to-Content Pipeline** — Enter a content idea and get polished, publish-ready output
- 🧠 **Analyze Agent** — Identifies target audience, objectives, content type, key messages, and requirements
- 📋 **Planning Agent** — Creates a structured content plan with tone, hooks, key points, and calls to action
- ✍️ **Creation Agent** — Generates high-quality content based on the analysis and plan, showing **only the generated content** (no review output mixed in)
- 🔍 **Review Agent** — Evaluates for relevance, clarity, quality, engagement, grammar, and accuracy with a structured visual report:
  - **Quality Score** — color-coded score out of 10 (green ≥ 8, amber ≥ 5, red below)
  - **Issues Found** — bullet list of problems identified in the draft
  - **Improvements Made** — bullet list of changes applied during review
  - **Approval** — clear `Approved` / `Needs Work` status badge
- 📄 **Final Output Section** — a dedicated, highlighted section showing the reviewed final content
- 📋 **Copy Content** — one-click copy buttons for the Creation Agent output and the Final Output (with fallback for older browsers)
- 📥 **Downloads** — download the full multi-agent report or just the final content as `.txt`
- 🔄 **Live Progress States** — stage-by-stage loading indicators for **Analyze → Plan → Create → Review** via Server-Sent Events streaming, with animated pipeline steps
- 🤖 **Google Gemini 3.6 Flash** — fast, state-of-the-art AI model for content generation
- ⚡ **FastAPI Backend** — Lightweight Python API with automatic retry logic for transient API errors
- 🎨 **React 19 Frontend** — Modern, dark-themed UI built with Vite 8
- 🐳 **Single-Container Deployment** — the backend serves the built frontend, so one service hosts the entire app (Docker + Render Blueprint ready)
- 📱 **Responsive Design** — Fully responsive layout for desktop and mobile

---

## 🔄 Autonomous AI Workflow

The system processes each idea through four specialized stages in two optimized Gemini API calls:

```text
User Idea
    │
    ▼
┌─────────────────┐
│  Analyze Agent   │  ─┐
│ Understand Idea  │   │  Gemini Call 1
└────────┬─────────┘   │
         │             │
         ▼             │
┌─────────────────┐   │
│ Planning Agent   │  ─┘
│ Create Strategy  │
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│ Creation Agent   │  ─┐
│ Generate Content │   │  Gemini Call 2
└────────┬─────────┘   │
         │             │
         ▼             │
┌─────────────────┐   │
│  Review Agent    │  ─┘
│ Score & Improve  │
└────────┬─────────┘
         │
         ▼
    Final Content
```

> **Optimization:** Agents are batched into two Gemini calls (Analyze + Plan, then Create + Review) to minimize latency while maintaining the multi-agent architecture.

---

## 🛠️ Tech Stack

| Layer      | Technology                | Version  |
| ---------- | ------------------------- | -------- |
| Frontend   | React                     | 19.2     |
| Bundler    | Vite                      | 8.2      |
| HTTP       | Fetch API (SSE streaming) | —        |
| Linter     | OxLint                    | 1.75     |
| Backend    | FastAPI                   | Latest   |
| AI Model   | Google Gemini 3.6 Flash   | Latest   |
| AI SDK     | Google GenAI Python SDK   | Latest   |
| Validation | Pydantic                  | Latest   |
| Env Loader | python-dotenv             | Latest   |
| Deploy     | Docker + Render (optional)| Latest   |

---

## 📁 Project Structure

```
autonomous-ai-creator/
├── .dockerignore               # Docker build exclusions
├── Dockerfile                  # Multi-stage: builds frontend, runs FastAPI + static frontend
├── README.md
├── render.yaml                 # Render Blueprint (one-click deployment config)
├── backend/
│   ├── main.py                 # FastAPI server with multi-agent pipeline + SSE streaming
│   ├── requirements.txt        # Python dependencies
│   └── .env                    # GEMINI_API_KEY (never committed)
└── frontend/
    ├── .oxlintrc.json          # OxLint configuration (React rules)
    ├── index.html              # HTML entry point
    ├── package.json            # Dependencies and scripts
    ├── vite.config.js          # Vite config + dev proxy to backend
    ├── public/
    │   ├── favicon.svg         # App favicon
    │   └── icons.svg           # Icon sprites
    └── src/
        ├── main.jsx            # React entry point (StrictMode)
        ├── index.css           # Global styles & CSS variables
        ├── App.jsx             # Main application component
        ├── App.css             # Component styles (dark theme)
        └── assets/
            ├── hero.png        # Hero section image
            ├── react.svg       # React logo
            └── vite.svg        # Vite logo
```

---

## ⚙️ Prerequisites

- **Python 3.10+** — [Download](https://www.python.org/downloads/)
- **Node.js 18+** — [Download](https://nodejs.org/) (Node 20.19+/22+ recommended for Vite 8)
- **Google Gemini API Key** — [Get one here](https://aistudio.google.com/apikey)

---

## 🏁 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/mukesh-2998/autonomous-ai-creator.git
cd autonomous-ai-creator
```

### 2. Set Up the Backend

```bash
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create a .env file with your Gemini API key
# NOTE: save it as plain UTF-8 WITHOUT a BOM, otherwise dotenv won't parse the key name
echo GEMINI_API_KEY=your_api_key_here > .env

# Start the backend server
uvicorn main:app --reload
```

The backend will start at **http://127.0.0.1:8000**.

### 3. Set Up the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will start at **http://localhost:5173**. Vite proxies `/generate` and `/generate-stream` to the backend on `127.0.0.1:8000`, so no extra CORS configuration is needed in development.

### 4. Open the App

Navigate to **http://localhost:5173**, enter a content idea, and click **"Generate Content →"**. Watch the pipeline progress: the Analyze, Plan, Create, and Review steps light up one by one while the results stream in live.

### 5. Production Build (optional)

```bash
cd frontend
npm run build        # outputs to frontend/dist
cd ..
cd backend
uvicorn main:app     # now also serves the built frontend at http://127.0.0.1:8000
```

---

## ⚡ Live Progress via SSE Streaming

The frontend no longer waits for one blocking request. It calls **`POST /generate-stream`** and consumes a **Server-Sent Events** stream (`fetch` + `ReadableStream` reader). Events arrive in this order:

```
analyzing → analyzed → planned → creating → created → reviewed → completed
```

Each event drives the UI:

| Event          | UI effect                                                    |
| -------------- | ------------------------------------------------------------ |
| `analyzing`    | Analyze step shows a spinner; status shows "Analyzing your idea..." |
| `analyzed`     | Analysis text renders; Analyze step turns green ✓; Plan step starts loading |
| `planned`      | Plan renders; Plan step turns green ✓; Create step starts loading |
| `creating`     | Create step spinner active                                    |
| `created`      | Creation Agent card shows only the generated content; Review step starts loading |
| `reviewed`     | Review card renders score / issues / improvements / approval  |
| `completed`    | All steps green ✓; Final Output section fills in; success badge appears |

The pipeline visualization (the numbers 1–4 near the bottom) mirrors the same states: **idle → pulsing purple (loading) → green ✓ (done)**.

> **Fallback:** if streaming fails for any reason, the frontend automatically retries against the non-streaming `POST /generate` endpoint so results are still delivered.

---

## 🔌 API Reference

### `GET /`

- Returns the built frontend (`index.html`) when a production build exists in `frontend/dist`.
- Otherwise returns the health message JSON.

```json
{
  "message": "Autonomous AI Creator backend is running"
}
```

---

### `GET /health`

Health check (used by deployment platforms like Render).

```json
{
  "status": "healthy"
}
```

---

### `POST /generate`

Non-streaming: generates content from a user idea through the multi-agent pipeline and returns everything in one response.

**Request Body:**

```json
{
  "idea": "Create a 7-day Instagram content plan about artificial intelligence"
}
```

**Success Response:**

```json
{
  "success": true,
  "idea": "Create a 7-day Instagram content plan about artificial intelligence",
  "status": "completed",
  "message": "Autonomous content workflow completed.",
  "analysis": "...",
  "plan": "...",
  "content": "...",
  "review": {
    "quality_score": 9,
    "strengths": [],
    "issues_found": ["...", "..."],
    "improvements_made": ["...", "..."],
    "status": "Approved",
    "raw": "..."
  },
  "final_content": "...",
  "pipeline": ["Analyze", "Plan", "Create", "Review"]
}
```

**Error Response (empty idea):**

```json
{
  "success": false,
  "message": "Please provide an idea."
}
```

---

### `POST /generate-stream`

**Server-Sent Events** version of `/generate`. Streams each pipeline stage so the frontend can show live progress. The response is a `text/event-stream` sequence of events:

```text
data: {"stage": "analyzing", "message": "Analyzing your idea..."}

data: {"stage": "analyzed", "message": "Analysis complete", "analysis": "..."}

data: {"stage": "planned", "message": "Content plan ready", "plan": "..."}

data: {"stage": "creating", "message": "Generating content..."}

data: {"stage": "created", "message": "Content generated", "content": "..."}

data: {"stage": "reviewed", "message": "Review complete", "review": {"quality_score": 9, "issues_found": [...], "improvements_made": [...], "status": "Approved"}}

data: {"stage": "completed", "message": "Autonomous content workflow completed.", "idea": "...", "analysis": "...", "plan": "...", "content": "...", "review": {...}, "final_content": "..."}

data: {"stage": "error", "message": "Generation failed: ..."}
```

---

## 🧪 How It Works — Under the Hood

### Gemini Call 1: Analyze + Plan

The first API call sends the user's idea to Gemini with a prompt that instructs it to:

1. **Analyze** the idea — identifying target audience, main objective, content type, key message, and requirements
2. **Plan** the content — defining structure, tone, key points, hook, and call to action

The response is parsed by splitting on `PLAN:` to separate the analysis from the plan.

### Gemini Call 2: Create + Review

The second API call sends the original idea, the analysis, and the content plan to Gemini with a prompt that instructs it to:

1. **Create** publish-ready content based on all prior context
2. **Review** the content for relevance, clarity, quality, engagement, grammar, call-to-action effectiveness, and accuracy — assigning a **quality score out of 10**

The response is parsed by splitting on `REVIEW:` to separate the created content from the review, and on `FINAL CONTENT:` to capture the improved final output.

### Review Parsing

The raw review text is parsed into structured fields (`parse_review` in `main.py`):

- `QUALITY SCORE: n/10` → `quality_score` (integer 0–10)
- `ISSUES FOUND:` / `ISSUES:` bullet lists → `issues_found`
- `IMPROVEMENTS MADE:` / `IMPROVEMENTS:` bullet lists → `improvements_made`
- `STATUS:` line → `status` (e.g. "Approved")

The UI renders these fields as a visual card: a big color-coded score, bulleted issue/improvement lists, and an approval badge.

### Retry Logic

Both Gemini calls use automatic retry logic (up to 3 attempts) for transient errors:

- `503 Service Unavailable`
- `UNAVAILABLE`
- `429 Too Many Requests`
- `RESOURCE_EXHAUSTED`

Permanent errors are raised immediately without retry.

---

## 🎨 Frontend UI

The frontend features a **dark-themed, modern UI** with:

- **Glassmorphic navbar** with a live system-online indicator
- **Hero section** with gradient text highlights
- **Idea input card** with a textarea and real-time status feedback
- **Live agent cards** — numbered 01–04, lighting up in sequence:
  - `01 Analyze Agent` — the idea analysis
  - `02 Planning Agent` — the content plan
  - `03 Creation Agent` — **only** the generated content (plus an inline Copy button)
  - `04 Review Agent` — the structured review popup (score, issues, improvements, approval)
- **Final Output** — a highlighted card with the reviewed, improved content, an approval badge, **Copy Content** button, and "Content Only" download
- **Pipeline visualization** — 4-step workflow with idle / loading / done states that animate during generation
- **Full Report download** — a nicely formatted `.txt` including every agent output
- **Responsive layout** that adapts to mobile viewports

---

## 🚢 Deployment

The project deploys as a **single Docker container** that serves both the FastAPI API and the built React frontend (FastAPI falls back to serving `frontend/dist` when it exists).

### Manual Build & Run

```bash
# Build the image (this runs npm ci + vite build, installs Python deps)
docker build -t autonomous-ai-creator .

# Run it (GEMINI_API_KEY must be set)
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_api_key_here \
  autonomous-ai-creator
```

### Render (one-click, free tier)

1. Push this repository to GitHub.
2. Go to [render.com](https://render.com) → **New +** → **Blueprint**.
3. Connect your GitHub repo (`autonomous-ai-creator`).
4. Render reads `render.yaml`, creates the web service, and builds from the `Dockerfile`.
5. On the service page, add the **GEMINI_API_KEY** secret environment variable.
6. Click **Apply** / **Deploy** — done.

`render.yaml` contents:

```yaml
services:
  - type: web
    name: autonomous-ai-creator
    runtime: docker
    dockerfilePath: ./Dockerfile
    plan: free
    healthCheckPath: /health
    envVars:
      - key: GEMINI_API_KEY
        sync: false
```

---

## 📝 Available Scripts

### Frontend

| Command           | Description                    |
| ----------------- | ------------------------------ |
| `npm run dev`     | Start Vite dev server          |
| `npm run build`   | Build for production           |
| `npm run preview` | Preview production build       |
| `npm run lint`    | Run OxLint                     |

### Backend

| Command                          | Description                          |
| -------------------------------- | ------------------------------------ |
| `uvicorn main:app --reload`      | Start FastAPI with hot reload        |
| `uvicorn main:app --port 8080`   | Start on a custom port               |

---

## 🔒 Environment Variables

| Variable          | Required | Description                |
| ----------------- | -------- | -------------------------- |
| `GEMINI_API_KEY`  | ✅       | Your Google Gemini API key |

Create a `.env` file in the `backend/` directory:

```env
GEMINI_API_KEY=your_api_key_here
```

> ⚠️ **Never commit your `.env` file.** It is already included in `.gitignore`.
> ⚠️ **Save it without a UTF-8 BOM** — tools like Windows Notepad sometimes add one, and python-dotenv will then read `\ufeffGEMINI_API_KEY` instead of the real name.

---

## 🙏 Acknowledgments

- [Google Gemini](https://deepmind.google/technologies/gemini/) — AI model powering content generation
- [FastAPI](https://fastapi.tiangolo.com/) — High-performance Python web framework
- [React](https://react.dev/) — UI library
- [Vite](https://vite.dev/) — Next-generation frontend build tool