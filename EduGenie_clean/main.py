"""EduGenie - Gemini powered learning assistant (FastAPI backend)."""
from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

import gemini_client
from explanation_module import explain_topic
from gemini_client import GeminiError
from learning_path import get_learning_recommendations
from qna import answer_question_with_gemini
from quiz_module import generate_quiz
from summary_module import summarize_text

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="EduGenie", description="Gemini powered learning assistant", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# ---------- request models ----------
class TopicRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)


class TextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)


class LearnRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
    level: str = Field("beginner", max_length=50)


# ---------- error handling ----------
@app.exception_handler(GeminiError)
async def gemini_error_handler(_: Request, exc: GeminiError):
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc)})


@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError):
    return JSONResponse(status_code=502, content={"error": str(exc)})


def _clean(value: str, what: str) -> str:
    value = value.strip()
    if not value:
        raise GeminiError(f"Please provide {what}.", status_code=400)
    return value


# ---------- pages ----------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "model": gemini_client.MODEL_NAME}


# ---------- API routes ----------
# Sync ("def") endpoints run in FastAPI's thread pool, so slow model calls
# never block the event loop. Both "/x" and "/x/" are accepted.

@app.get("/qa")
def answer_question(question: str = Query(..., min_length=1, max_length=1000)):
    question = _clean(question, "a question")
    return {"answer": answer_question_with_gemini(question)}


@app.post("/explain")
@app.post("/explain/", include_in_schema=False)
def explain_api(body: TopicRequest):
    topic = _clean(body.topic, "a topic")
    return {"topic": topic, "explanation": explain_topic(topic)}


@app.post("/summarize")
@app.post("/summarize/", include_in_schema=False)
def summarize_api(body: TextRequest):
    text = _clean(body.text, "text to summarize")
    return {"summary": summarize_text(text)}


@app.post("/quiz")
@app.post("/quiz/", include_in_schema=False)
def quiz_api(body: TextRequest):
    text = _clean(body.text, "a topic or passage")
    return {"quiz": generate_quiz(text)}


@app.post("/learn/recommendations")
@app.post("/learn/recommendations/", include_in_schema=False)
def learn_api(body: LearnRequest):
    topic = _clean(body.topic, "a topic")
    return {"topic": topic, "recommendations": get_learning_recommendations(topic, body.level)}
