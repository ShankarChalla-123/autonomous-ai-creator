# 🤖 Autonomous AI Creator

Autonomous AI Creator is an AI-powered content creation system that takes a user's idea and turns it into structured, publish-ready content.

Instead of relying on a single AI prompt, the system uses multiple specialized agents. Each agent handles a different stage of the workflow: understanding the idea, planning the content, creating it, and reviewing the final result.

---

## 🚀 Features

- 💡 Enter a content idea through the web interface
- 🧠 Analyze Agent understands the idea and its requirements
- 📋 Planning Agent creates a structured content plan
- ✍️ Creation Agent generates the requested content
- 🔍 Review Agent checks and improves the generated content
- 🤖 Google Gemini API for AI-powered generation
- ⚡ FastAPI backend for processing requests
- 🎨 React frontend for user interaction
- 🔄 Multi-agent autonomous workflow
- 🌐 REST API communication between frontend and backend

---

## 🔄 Autonomous AI Workflow

The system processes each idea through four specialized stages:

```text
User Idea
    │
    ▼
┌─────────────────┐
│  Analyze Agent  │
│ Understand Idea │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Planning Agent  │
│ Create Strategy │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Creation Agent  │
│ Generate Content│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Review Agent  │
│ Check & Improve │
└────────┬────────┘
         │
         ▼
    Final Content
