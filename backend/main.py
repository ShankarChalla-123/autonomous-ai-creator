import time
import os

from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai


# ==========================================
# LOAD ENVIRONMENT
# ==========================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing from .env")

client = genai.Client(
    api_key=api_key
)


# ==========================================
# FASTAPI APP
# ==========================================

app = FastAPI(title="Autonomous AI Creator")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# REQUEST MODEL
# ==========================================

class CreationRequest(BaseModel):
    idea: str


# ==========================================
# ROOT
# ==========================================

@app.get("/")
def root():
    return {
        "message": "Autonomous AI Creator backend is running"
    }


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ==========================================
# GEMINI HELPER
# ==========================================

def generate_with_retry(prompt, agent_name):

    for attempt in range(3):

        try:

            print(
                f"{agent_name} attempt {attempt + 1}/3..."
            )

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )

            print(
                f"{agent_name} completed successfully."
            )

            return response.text

        except Exception as error:

            error_text = str(error)

            print(
                f"{agent_name} attempt {attempt + 1} failed:"
            )

            print(error)

            # Retry only temporary API problems
            if (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
            ):

                if attempt < 2:

                    print(
                        "Temporary Gemini error."
                        " Retrying in 5 seconds..."
                    )

                    time.sleep(5)

                else:

                    raise error

            else:

                # Permanent errors should not be retried
                raise error

    return None


# ==========================================
# GENERATE CONTENT
# ==========================================

@app.post("/generate")
def generate_content(request: CreationRequest):

    idea = request.idea.strip()

    if not idea:

        return {
            "success": False,
            "message": "Please provide an idea."
        }


    # ==========================================
    # GEMINI CALL 1
    # ANALYZE + PLAN
    # ==========================================

    planning_prompt = f"""
You are the Analyze and Planning Agent in an autonomous AI
content creation system.

User idea:
{idea}

First ANALYZE the idea.

Identify:

1. Target audience
2. Main objective
3. Content type
4. Key message
5. Important requirements

Then create a CONTENT PLAN.

Include:

1. Structure
2. Tone
3. Key points
4. Hook
5. Call to action

Return EXACTLY in this format:

ANALYSIS:
[Write the analysis here]

PLAN:
[Write the content plan here]
"""

    planning_text = generate_with_retry(
        planning_prompt,
        "Analyze + Planning Agent"
    )


    # ==========================================
    # SEPARATE ANALYSIS AND PLAN
    # ==========================================

    analysis = planning_text
    plan = planning_text

    if "PLAN:" in planning_text:

        parts = planning_text.split(
            "PLAN:",
            1
        )

        analysis = parts[0].replace(
            "ANALYSIS:",
            ""
        ).strip()

        plan = parts[1].strip()


    # ==========================================
    # GEMINI CALL 2
    # CREATE + REVIEW
    # ==========================================

    creation_prompt = f"""
You are the Creation and Review Agent in an autonomous AI
content creation system.

USER IDEA:
{idea}

ANALYSIS:
{analysis}

CONTENT PLAN:
{plan}

You have TWO responsibilities.

STAGE 1 - CREATE

Create high-quality, ready-to-publish content based on the
user idea, analysis, and content plan.

STAGE 2 - REVIEW

Review the created content for:

1. Relevance
2. Clarity
3. Quality
4. Engagement
5. Grammar
6. Call to action
7. Accuracy

Identify problems and improve the content.

Return EXACTLY in this format:

CREATED CONTENT:
[Write only the original created content here]

REVIEW:
QUALITY SCORE: [score]/10

STRENGTHS:
- [strength 1]
- [strength 2]
- [strength 3]

ISSUES FOUND:
- [issue 1]
- [issue 2]

IMPROVEMENTS MADE:
- [improvement 1]
- [improvement 2]

STATUS:
Approved

FINAL CONTENT:
[Write the improved final content here]
"""

    creation_text = generate_with_retry(
        creation_prompt,
        "Creation + Review Agent"
    )


    # ==========================================
    # SEPARATE CONTENT AND REVIEW
    # ==========================================

    content = creation_text
    review = creation_text

    if "REVIEW:" in creation_text:

        content_parts = creation_text.split(
            "REVIEW:",
            1
        )

        content = content_parts[0].replace(
            "CREATED CONTENT:",
            ""
        ).strip()

        review = (
            "REVIEW:"
            + content_parts[1].strip()
        )


    # ==========================================
    # FINAL RESPONSE
    # ==========================================

    return {
        "success": True,

        "idea": idea,

        "status": "completed",

        "message": (
            "Autonomous content workflow completed."
        ),

        "analysis": analysis,

        "plan": plan,

        "content": content,

        "review": review,

        "pipeline": [
            "Analyze",
            "Plan",
            "Create",
            "Review"
        ]
    }