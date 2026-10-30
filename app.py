
import os
import json
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel
from pypdf import PdfReader

load_dotenv()

# ---------------- APP CONFIGURATION ----------------

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# Create static folder automatically if it does not exist.
STATIC_DIR.mkdir(exist_ok=True)
print("APP FILE:", __file__)
print("IMAGE FOLDER:", STATIC_DIR)
print("IMAGE EXISTS:", (STATIC_DIR / "welcome-ai.png").exists())
app = FastAPI(title="AI Voice Teacher")

# Serve images and other static files.
# Welcome image URL: /static/welcome-ai.png
app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)

# ---------------- GROQ API CONFIGURATION ----------------

api_key = os.getenv("GROQ_API_KEY")

client = (
    OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )
    if api_key else None
)

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


# ---------------- REQUEST MODELS ----------------

class ExplanationRequest(BaseModel):
    question: str
    language: str = "English"
    level: str = "Beginner"


class FollowUpRequest(BaseModel):
    question: str
    previous_explanation: str
    language: str = "English"
    level: str = "Beginner"


class QuizRequest(BaseModel):
    topic: str
    explanation: str
    language: str = "English"


class FlashcardsRequest(BaseModel):
    topic: str
    explanation: str
    language: str = "English"


# ---------------- VALIDATION ----------------

SUPPORTED_LANGUAGES = [
    "English",
    "Telugu",
    "Telugu + English"
]

SUPPORTED_LEVELS = [
    "Beginner",
    "Intermediate",
    "Advanced"
]


def validate_settings(language, level):
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail="Choose English, Telugu, or Telugu + English."
        )

    if level not in SUPPORTED_LEVELS:
        raise HTTPException(
            status_code=400,
            detail="Invalid learning level."
        )


def language_instruction(language):
    instructions = {
        "English": (
            "Explain in simple, clear English."
        ),
        "Telugu": (
            "Explain in Telugu. Keep technical terms in English "
            "where helpful and explain them simply."
        ),
        "Telugu + English": (
            "Use a natural mix of Telugu and English. "
            "Keep technical terms in English and explain them "
            "in simple Telugu-English."
        )
    }

    return instructions[language]


# ---------------- COMMON AI FUNCTION ----------------

def ask_ai(prompt, max_tokens=1800):
    if client is None:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY missing. Check your .env file."
        )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=max_tokens
        )

        answer = response.choices[0].message.content

        if not answer or not answer.strip():
            raise ValueError("AI returned an empty response.")

        return answer.strip()

    except HTTPException:
        raise

    except Exception as error:
        print("AI ERROR DETAILS:", repr(error))

        raise HTTPException(
            status_code=502,
            detail="AI request failed. Check the VS Code terminal."
        )


# ---------------- HOME & LOGIN PAGES ----------------

@app.get("/")
def home():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/login")
def login_page():
    return FileResponse(BASE_DIR / "index.html")


class AuthRequest(BaseModel):
    username: str
    password: str


@app.post("/api/login")
def api_login(data: AuthRequest):
    username = data.username.strip()
    password = data.password.strip()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username is required."
        )

    if not password:
        raise HTTPException(
            status_code=400,
            detail="Password is required."
        )

    if len(password) < 4:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 4 characters."
        )

    return {
        "status": "success",
        "message": "Login successful",
        "username": username
    }


@app.post("/api/register")
def api_register(data: AuthRequest):
    username = data.username.strip()
    password = data.password.strip()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username is required."
        )

    if not password:
        raise HTTPException(
            status_code=400,
            detail="Password is required."
        )

    if len(password) < 4:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 4 characters."
        )

    return {
        "status": "success",
        "message": "Registration successful",
        "username": username
    }


# ---------------- EXPLAIN A CONCEPT ----------------

@app.post("/explain")
def explain(data: ExplanationRequest):
    question = data.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Please enter a question."
        )

    validate_settings(data.language, data.level)

    prompt = f"""
You are a friendly, patient AI teacher.

Language instructions:
{language_instruction(data.language)}

Student learning level: {data.level}

Explain the student's question using this structure:

1. Simple definition
2. Step-by-step explanation
3. One easy example
4. Code and expected output, if relevant
5. Important points
6. Short summary

Use clear headings and bullet points.
Explain difficult terms in simple language.
Avoid unnecessary repetition.
Do not claim to execute code.

Student question:
{question[:3000]}
"""

    return {
        "explanation": ask_ai(prompt)
    }


# ---------------- FOLLOW-UP QUESTION ----------------

@app.post("/followup")
def followup(data: FollowUpRequest):
    question = data.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Enter your follow-up question."
        )

    validate_settings(data.language, data.level)

    prompt = f"""
You are a patient AI teacher.

Language instructions:
{language_instruction(data.language)}

Student learning level: {data.level}

Previous explanation:
{data.previous_explanation[:10000]}

Student follow-up question:
{question[:3000]}

Explain the confusing part clearly.
Use simple steps and a new example.
Use headings and bullet points when helpful.
Finish with one important point to remember.
"""

    return {
        "explanation": ask_ai(prompt)
    }


# ---------------- GENERATE QUIZ ----------------

@app.post("/quiz")
def quiz(data: QuizRequest):
    if not data.topic.strip() or not data.explanation.strip():
        raise HTTPException(
            status_code=400,
            detail="Generate a lesson before creating a quiz."
        )

    if data.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail="Invalid language."
        )

    prompt = f"""
Create exactly 5 multiple-choice questions.

Language instructions:
{language_instruction(data.language)}

Topic:
{data.topic[:300]}

Use only this lesson:
{data.explanation[:10000]}

Return only valid JSON in this format:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": [
        "Option A",
        "Option B",
        "Option C",
        "Option D"
      ],
      "answer": 0,
      "reason": "Short explanation"
    }}
  ]
}}

Requirements:
- Exactly 5 questions.
- Exactly 4 options per question.
- Answer must be an integer from 0 to 3.
- Reason must briefly explain the correct answer.
- Do not include Markdown fences.
"""

    raw = ask_ai(prompt, max_tokens=2200)

    try:
        start = raw.find("{")
        end = raw.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("No JSON found.")

        result = json.loads(raw[start:end + 1])
        questions = result["questions"]

        if not isinstance(questions, list) or len(questions) != 5:
            raise ValueError("Expected five questions.")

        for item in questions:
            if (
                not isinstance(item.get("question"), str)
                or not isinstance(item.get("options"), list)
                or len(item["options"]) != 4
                or not all(
                    isinstance(option, str)
                    for option in item["options"]
                )
                or type(item.get("answer")) is not int
                or item["answer"] not in range(4)
                or not isinstance(item.get("reason"), str)
            ):
                raise ValueError("Invalid quiz format.")

        return {"questions": questions}

    except (
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError
    ):
        raise HTTPException(
            status_code=502,
            detail="Quiz generation failed. Please try again."
        )


# ---------------- AI FLASHCARDS ----------------

@app.post("/flashcards")
def generate_flashcards(data: FlashcardsRequest):
    if not data.topic.strip() or not data.explanation.strip():
        raise HTTPException(
            status_code=400,
            detail="Generate a lesson before creating flashcards."
        )

    if data.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail="Invalid language."
        )

    prompt = f"""
You are a friendly AI teacher.

Create exactly 8 study flashcards.

Language instructions:
{language_instruction(data.language)}

Topic:
{data.topic[:300]}

Use only this lesson:
{data.explanation[:10000]}

Return only valid JSON:
{{
  "flashcards": [
    {{
      "question": "Short question",
      "answer": "Simple answer"
    }}
  ]
}}

Rules:
- Create exactly 8 flashcards.
- Keep questions short and useful for revision.
- Answers must be easy to understand.
- Use only information from the lesson.
- Do not include Markdown fences.
"""

    raw = ask_ai(prompt, max_tokens=2000)

    try:
        start = raw.find("{")
        end = raw.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("No JSON found.")

        result = json.loads(raw[start:end + 1])
        cards = result["flashcards"]

        if not isinstance(cards, list) or len(cards) != 8:
            raise ValueError("Expected eight flashcards.")

        for card in cards:
            if (
                not isinstance(card.get("question"), str)
                or not isinstance(card.get("answer"), str)
                or not card["question"].strip()
                or not card["answer"].strip()
            ):
                raise ValueError("Invalid flashcard.")

        return {"flashcards": cards}

    except (
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError
    ):
        raise HTTPException(
            status_code=502,
            detail="Flashcard generation failed. Please try again."
        )


# ---------------- EXPLAIN AN UPLOADED PDF ----------------

@app.post("/pdf-explain")
async def pdf_explain(
    file: UploadFile = File(...),
    language: str = "English",
    level: str = "Beginner"
):
    if (
        not file.filename
        or not file.filename.lower().endswith(".pdf")
    ):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF file."
        )

    validate_settings(language, level)

    content = await file.read(5 * 1024 * 1024 + 1)

    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="PDF must be 5 MB or smaller."
        )

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF is empty."
        )

    try:
        reader = PdfReader(BytesIO(content))

        if reader.is_encrypted:
            raise HTTPException(
                status_code=400,
                detail="Password-protected PDFs are not supported."
            )

        if len(reader.pages) > 30:
            raise HTTPException(
                status_code=400,
                detail="PDF must contain 30 pages or fewer."
            )

        pdf_text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        ).strip()

    except HTTPException:
        raise

    except Exception as error:
        print("PDF READING ERROR:", repr(error))

        raise HTTPException(
            status_code=400,
            detail="Could not read this PDF. Please try another file."
        )

    if not pdf_text:
        raise HTTPException(
            status_code=400,
            detail="No selectable text found. Scanned PDFs need OCR."
        )

    prompt = f"""
You are an excellent, friendly, patient AI teacher.

Teach the content of the uploaded PDF accurately.

Language instructions:
{language_instruction(language)}

Student learning level: {level}

Use simple words and do not invent facts.

Organize the explanation like this:

# PDF Explanation

## 1. Overview
Describe what the PDF covers in 2 to 4 sentences.

## 2. Important Topics
Explain each major topic under a separate heading.
For relevant topics include:
- Definition
- Step-by-step explanation
- Easy practical example
- Code and expected output, if relevant
- Key point to remember

## 3. Important Points
List the important facts.

## 4. Quick Revision
Provide short revision notes.

## 5. Practice Questions
Create 3 short questions without their answers.

## 6. Summary
Summarize the whole PDF simply.

Use clear headings and short paragraphs.
Do not repeat the entire PDF word for word.

PDF content:
{pdf_text[:18000]}
"""

    explanation = ask_ai(prompt, max_tokens=2800)

    return {
        "filename": file.filename,
        "language": language,
        "level": level,
        "explanation": explanation
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
