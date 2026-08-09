# PROMPTS.md

## Autonomous AI Creator - AI Usage Log

This file records the AI-assisted prompts and development conversations used while building the project. The project was developed iteratively with AI assistance, with the generated code tested locally before being committed.

## 1. Project Selection and Architecture

### Prompt
> Project: Autonomous AI Creator. Concept: Idea → content pipeline. Enter an idea, get analyzed/planned/created/reviewed content with live progress, a quality score, and a downloadable report.

### AI-assisted architecture discussion
The project was reviewed as a React 19 + Vite frontend and FastAPI backend. The workflow was defined around four logical stages:
- Analyze
- Plan
- Create
- Review

The backend exposes health, non-streaming generation, and SSE streaming endpoints. Gemini is used for generation.

## 2. Initial Quality and Security Review

### Prompt
> What changes or modifications are needed, and what are the next steps?

### AI-assisted review
The project was reviewed for:
- Fragile marker-based Gemini parsing
- Prompt injection
- Rate limiting
- Authentication
- Error handling
- Logging
- Duplicated backend logic
- Testing
- Deployment readiness

The highest-priority risks identified were parsing brittleness, prompt injection, and unrestricted access to the paid Gemini endpoint.

## 3. Backend Security Improvements

### Prompt used with the coding agent
> Improve the Autonomous AI Creator backend security and robustness. Add input validation, prompt-injection resistance, rate limiting, safe errors, structured logging, and automated tests without changing the existing response schema or frontend workflow.

### Resulting changes
- Added a 4000-character maximum idea length.
- Rejected empty and whitespace-only ideas.
- Delimited user ideas in prompts using `<user_idea>` tags.
- Added explicit prompt instructions that user content is data, not instructions.
- Added an in-memory per-IP sliding-window rate limiter.
- Added generic client-facing error messages.
- Replaced `print()` calls with logging.
- Added environment-configurable limits.
- Added security and pipeline tests.

## 4. Authentication Feature

### Prompt used with the coding agent
> Add login and register pages to the Autonomous AI Creator. Use SQLite for users, secure password hashing, JWT authentication, `/auth/register`, `/auth/login`, and `/auth/me`. Require authentication for content generation while preserving the existing creator UI and API response fields.

### Resulting changes
Backend:
- `backend/auth.py`
- SQLite user database
- Password hashing with `pwdlib`/bcrypt
- JWT authentication
- `/auth/register`
- `/auth/login`
- `/auth/me`
- Authentication dependency for generation endpoints

Frontend:
- `frontend/src/AuthContext.jsx`
- `frontend/src/Login.jsx`
- `frontend/src/Register.jsx`
- `frontend/src/api.js`
- Authentication gate in `App.jsx`
- User chip and logout
- Bearer token handling

## 5. Authentication Testing

### Prompt / verification request
> Test the authentication implementation end-to-end and verify registration, duplicate registration, login, invalid credentials, `/auth/me`, protected generation endpoints, token expiry, and frontend build/lint.

### Result
The authentication and existing backend test suite reached:
- 61 tests passed
- Frontend lint passed
- Frontend build passed
- Live registration and authentication were verified

## 6. Gemini Integration Debugging

### Problem observed
The frontend initially reported a generic generation failure.

The backend log showed:
`401 UNAUTHENTICATED`
`ACCESS_TOKEN_TYPE_UNSUPPORTED`

The AI-assisted debugging process identified that authentication with the Gemini credential, rather than the React authentication system, was the failing part.

### Verification
- `/auth/me` returned HTTP 200.
- `/auth/register` returned HTTP 200.
- `/generate-stream` reached the FastAPI backend.
- The Gemini request was the failing operation.

A new Gemini credential was configured and the backend/frontend were restarted.

## 7. Final End-to-End Verification

### Test idea
> Create a LinkedIn post explaining why college students should learn Python, SQL, and AI.

### Result
The content pipeline successfully generated output after the Gemini authentication issue was resolved.

Verified workflow:

Register → Login → Enter Idea → Analyze → Plan → Create → Review → Final Content

## 8. Development Tools / AI-Assisted Workflow

The project was developed and modified using AI-assisted coding workflows, including Antigravity/OpenCode-style coding-agent sessions, with local testing in PowerShell, VS Code/Antigravity, React/Vite, FastAPI, pytest, and Git.

## 9. Git / Submission Preparation

The project was committed and pushed to the public GitHub repository.

The working tree was verified clean with:

```text
Your branch is up to date with 'origin/main'.
nothing to commit, working tree clean
```

The local `backend/users.db` database was intentionally not committed. Environment files containing secrets are also excluded from Git.

## 10. Submission Checklist

Required submission artifacts:

- Public GitHub repository
- Live deployed URL
- This `PROMPTS.md` at repository root

Do not commit API keys, JWT secrets, local databases, or other secrets.

