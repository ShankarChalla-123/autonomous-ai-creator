import time
import os
import json
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
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
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Location of the built frontend (frontend/dist)
FRONTEND_DIST = (
    Path(__file__).resolve().parent.parent
    / "frontend"
    / "dist"
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
    index = FRONTEND_DIST / "index.html"
    if index.is_file():
        return FileResponse(index)
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
# PARSE REVIEW INTO STRUCTURED DATA
# ==========================================

def parse_review(review_text):
    """Parse review text into structured fields."""

    result = {
        "quality_score": None,
        "strengths": [],
        "issues_found": [],
        "improvements_made": [],
        "status": None,
        "raw": review_text
    }

    if not review_text:
        return result

    # Extract quality score
    score_match = re.search(
        r"QUALITY\s*SCORE:\s*(\d+)\s*/\s*10",
        review_text,
        re.IGNORECASE
    )
    if score_match:
        result["quality_score"] = int(score_match.group(1))

    # Helper: extract bullet-point lists between markers
    def extract_list(text, start_marker, stop_markers):

        upper = text.upper()
        marker_upper = start_marker.upper()

        if marker_upper not in upper:
            return []

        start = upper.index(marker_upper) + len(marker_upper)

        end = len(text)
        for stop in stop_markers:
            pos = upper.find(stop.upper(), start)
            if pos != -1 and pos < end:
                end = pos

        section = text[start:end]
        items = []
        for line in section.strip().split("\n"):
            stripped = line.strip()
            if stripped.startswith("- "):
                items.append(stripped[2:].strip())
            elif stripped.startswith("* "):
                items.append(stripped[2:].strip())
        return items

    end_markers = [
        "STRENGTHS:", "ISSUES FOUND:", "ISSUES:",
        "IMPROVEMENTS MADE:", "IMPROVEMENTS:",
        "STATUS:", "FINAL CONTENT:"
    ]

    result["strengths"] = extract_list(
        review_text, "STRENGTHS:",
        [m for m in end_markers if m != "STRENGTHS:"]
    )

    result["issues_found"] = extract_list(
        review_text, "ISSUES FOUND:",
        [m for m in end_markers
         if m not in ("ISSUES FOUND:", "ISSUES:", "STRENGTHS:")]
    )
    if not result["issues_found"]:
        result["issues_found"] = extract_list(
            review_text, "ISSUES:",
            [m for m in end_markers
             if m not in ("ISSUES:", "ISSUES FOUND:", "STRENGTHS:")]
        )

    result["improvements_made"] = extract_list(
        review_text, "IMPROVEMENTS MADE:",
        ["STATUS:", "FINAL CONTENT:"]
    )
    if not result["improvements_made"]:
        result["improvements_made"] = extract_list(
            review_text, "IMPROVEMENTS:",
            ["STATUS:", "FINAL CONTENT:"]
        )

    # Extract status
    status_match = re.search(
        r"STATUS:\s*(.+)",
        review_text,
        re.IGNORECASE
    )
    if status_match:
        result["status"] = status_match.group(1).strip()

    return result


# ==========================================
# SSE HELPER
# ==========================================

def sse_event(data):
    """Format data dict as a Server-Sent Event line."""
    return f"data: {json.dumps(data)}\n\n"


# ==========================================
# STREAMING GENERATE ENDPOINT
# ==========================================

@app.post("/generate-stream")
def generate_content_stream(request: CreationRequest):

    idea = request.idea.strip()

    if not idea:

        def error_stream():
            yield sse_event({
                "stage": "error",
                "message": "Please provide an idea."
            })

        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )

    def event_generator():

        try:

            # ================================
            # STAGE: ANALYZING
            # ================================

            yield sse_event({
                "stage": "analyzing",
                "message": "Analyzing your idea..."
            })

            # GEMINI CALL 1: ANALYZE + PLAN
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

            # Separate analysis and plan
            analysis = planning_text
            plan = planning_text

            if "PLAN:" in planning_text:
                parts = planning_text.split("PLAN:", 1)
                analysis = parts[0].replace(
                    "ANALYSIS:", ""
                ).strip()
                plan = parts[1].strip()

            # ================================
            # STAGE: ANALYZED
            # ================================

            yield sse_event({
                "stage": "analyzed",
                "message": "Analysis complete",
                "analysis": analysis
            })

            time.sleep(0.5)

            # ================================
            # STAGE: PLANNED
            # ================================

            yield sse_event({
                "stage": "planned",
                "message": "Content plan ready",
                "plan": plan
            })

            time.sleep(0.3)

            # ================================
            # STAGE: CREATING
            # ================================

            yield sse_event({
                "stage": "creating",
                "message": "Generating content..."
            })

            # GEMINI CALL 2: CREATE + REVIEW
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

            # ================================
            # PARSE CONTENT, REVIEW, FINAL
            # ================================

            created_content = creation_text
            review_text = ""
            final_content = ""

            if "REVIEW:" in creation_text:
                content_parts = creation_text.split(
                    "REVIEW:", 1
                )
                created_content = content_parts[0].replace(
                    "CREATED CONTENT:", ""
                ).strip()
                review_text = (
                    "REVIEW:" + content_parts[1].strip()
                )

            if "FINAL CONTENT:" in creation_text:
                final_parts = creation_text.split(
                    "FINAL CONTENT:", 1
                )
                final_content = final_parts[1].strip()
            else:
                final_content = created_content

            review_data = parse_review(review_text)

            # ================================
            # STAGE: CREATED
            # ================================

            yield sse_event({
                "stage": "created",
                "message": "Content generated",
                "content": created_content
            })

            time.sleep(0.5)

            # ================================
            # STAGE: REVIEWED
            # ================================

            yield sse_event({
                "stage": "reviewed",
                "message": "Review complete",
                "review": review_data
            })

            time.sleep(0.3)

            # ================================
            # STAGE: COMPLETED
            # ================================

            yield sse_event({
                "stage": "completed",
                "message":
                    "Autonomous content workflow completed.",
                "idea": idea,
                "analysis": analysis,
                "plan": plan,
                "content": created_content,
                "review": review_data,
                "final_content": final_content,
                "pipeline": [
                    "Analyze", "Plan", "Create", "Review"
                ]
            })

        except Exception as error:

            yield sse_event({
                "stage": "error",
                "message": f"Generation failed: {str(error)}"
            })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


# ==========================================
# GENERATE CONTENT (original endpoint)
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
    # SEPARATE CONTENT, REVIEW, FINAL
    # ==========================================

    content = creation_text
    review_text = ""
    final_content = ""

    if "REVIEW:" in creation_text:

        content_parts = creation_text.split(
            "REVIEW:",
            1
        )

        content = content_parts[0].replace(
            "CREATED CONTENT:",
            ""
        ).strip()

        review_text = (
            "REVIEW:"
            + content_parts[1].strip()
        )

    if "FINAL CONTENT:" in creation_text:
        final_parts = creation_text.split(
            "FINAL CONTENT:", 1
        )
        final_content = final_parts[1].strip()
    else:
        final_content = content

    review_data = parse_review(review_text)


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

        "review": review_data,

        "final_content": final_content,

        "pipeline": [
            "Analyze",
            "Plan",
            "Create",
            "Review"
        ]
    }


# ==========================================
# SERVE BUILT FRONTEND (production)
# Serves the Vite build from frontend/dist
# when it exists, so one host runs the app.
# ==========================================

if FRONTEND_DIST.is_dir():

    app.mount(
        "/assets",
        StaticFiles(
            directory=FRONTEND_DIST / "assets"
        ),
        name="assets",
    )

    @app.get("/{full_path:path}")
    def spa(full_path: str):

        target = (FRONTEND_DIST / full_path).resolve()

        if (
            target.is_file()
            and str(target).startswith(
                str(FRONTEND_DIST.resolve())
            )
        ):
            return FileResponse(target)

        index = FRONTEND_DIST / "index.html"
        if index.is_file():
            return FileResponse(index)

        return {
            "message":
                "Frontend not built. "
                "Run `npm run build` in frontend/."
        }