# 🤖 Autonomous AI Creator

An AI-powered content creation system that transforms a single idea into structured, publish-ready content using a **multi-agent autonomous pipeline**. Instead of relying on one monolithic prompt, the system orchestrates four specialized AI agents — **Analyze → Plan → Create → Review** — each handling a distinct stage of the content workflow.

Built with a **React + Vite** frontend and a **FastAPI** backend, powered by the **Google Gemini API**.

---

## 🚀 Features

- 💡 **Idea-to-Content Pipeline** — Enter a content idea and get polished, publish-ready output
- 🧠 **Analyze Agent** — Identifies target audience, objectives, content type, key messages, and requirements
- 📋 **Planning Agent** — Creates a structured content plan with tone, hooks, key points, and calls to action
- ✍️ **Creation Agent** — Generates high-quality content based on the analysis and plan
- 🔍 **Review Agent** — Evaluates for relevance, clarity, quality, engagement, grammar, and accuracy with a quality score
- 🤖 **Google Gemini 3.6 Flash** — Fast, state-of-the-art AI model for content generation
- ⚡ **FastAPI Backend** — Lightweight Python API with automatic retry logic for transient API errors
- 🎨 **React 19 Frontend** — Modern, dark-themed UI built with Vite 8
- 🔄 **Multi-Agent Workflow** — Autonomous pipeline with no manual intervention between stages
- 🌐 **REST API** — Clean JSON communication between frontend and backend
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
│ Check & Improve  │
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
| HTTP Client| Axios                     | 1.19     |
| Icons      | Lucide React              | 1.30     |
| Routing    | React Router DOM          | 7.18     |
| Linter     | OxLint                    | 1.75     |
| Backend    | FastAPI                   | Latest   |
| AI Model   | Google Gemini 3.6 Flash   | Latest   |
| AI SDK     | Google GenAI Python SDK   | Latest   |
| Validation | Pydantic                  | Latest   |
| Env Loader | python-dotenv             | Latest   |

---

## 📁 Project Structure

```
autonomous-ai-creator/
├── .gitignore
├── README.md
├── backend/
│   └── main.py                  # FastAPI server with multi-agent pipeline
└── frontend/
    ├── .gitignore
    ├── .oxlintrc.json           # OxLint configuration (React rules)
    ├── index.html               # HTML entry point
    ├── package.json             # Dependencies and scripts
    ├── vite.config.js           # Vite configuration
    ├── public/
    │   ├── favicon.svg          # App favicon
    │   └── icons.svg            # Icon sprites
    └── src/
        ├── main.jsx             # React entry point (StrictMode)
        ├── index.css            # Global styles & CSS variables
        ├── App.jsx              # Main application component
        ├── App.css              # Component styles (dark theme)
        └── assets/
            ├── hero.png         # Hero section image
            ├── react.svg        # React logo
            └── vite.svg         # Vite logo
```

---

## ⚙️ Prerequisites

- **Python 3.10+** — [Download](https://www.python.org/downloads/)
- **Node.js 18+** — [Download](https://nodejs.org/)
- **Google Gemini API Key** — [Get one here](https://aistudio.google.com/apikey)

---

## 🏁 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/autonomous-ai-creator.git
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
pip install fastapi uvicorn python-dotenv google-genai pydantic

# Create a .env file with your Gemini API key
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

The frontend will start at **http://localhost:5173**.

### 4. Open the App

Navigate to **http://localhost:5173** in your browser, enter a content idea, and click **"Generate Content →"**.

---

## 🔌 API Reference

### `GET /`

Health message confirming the backend is running.

**Response:**
```json
{
  "message": "Autonomous AI Creator backend is running"
}
```

---

### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

---

### `POST /generate`

Generate content from a user idea through the multi-agent pipeline.

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
  "review": "...",
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

## 🧪 How It Works — Under the Hood

### Gemini Call 1: Analyze + Plan

The first API call sends the user's idea to Gemini with a prompt that instructs it to:

1. **Analyze** the idea — identifying target audience, main objective, content type, key message, and requirements
2. **Plan** the content — defining structure, tone, key points, hook, and call to action

The response is parsed by splitting on `PLAN:` to separate the analysis from the plan.

### Gemini Call 2: Create + Review

The second API call sends the original idea, the analysis, and the content plan to Gemini with a prompt that instructs it to:

1. **Create** publish-ready content based on all prior context
2. **Review** the content for relevance, clarity, quality, engagement, grammar, call-to-action effectiveness, and accuracy — assigning a quality score out of 10

The response is parsed by splitting on `REVIEW:` to separate the created content from the review.

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
- **Agent output cards** displaying results from each of the four agents (Analyze, Plan, Create, Review) with numbered badges
- **Pipeline visualization** showing the four-step autonomous workflow
- **Responsive layout** that adapts to mobile viewports

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

| Command                          | Description                    |
| -------------------------------- | ------------------------------ |
| `uvicorn main:app --reload`      | Start FastAPI with hot reload  |

---

## 🔒 Environment Variables

| Variable         | Required | Description                              |
| ---------------- | -------- | ---------------------------------------- |
| `GEMINI_API_KEY`  | ✅       | Your Google Gemini API key               |

Create a `.env` file in the `backend/` directory:

```env
GEMINI_API_KEY=your_api_key_here
```

> ⚠️ **Never commit your `.env` file.** It is already included in `.gitignore`.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🙏 Acknowledgments

- [Google Gemini](https://deepmind.google/technologies/gemini/) — AI model powering content generation
- [FastAPI](https://fastapi.tiangolo.com/) — High-performance Python web framework
- [React](https://react.dev/) — UI library
- [Vite](https://vite.dev/) — Next-generation frontend build tool
