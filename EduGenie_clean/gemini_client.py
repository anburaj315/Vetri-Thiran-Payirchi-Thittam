"""Shared Google Gemini client used by every cloud-powered module.

Handles temporary overloads (503/429) by retrying, then switching to backup models.
"""
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load .env from the project folder, no matter where the terminal is
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# Backup models, tried in order if the main model is busy or not available
FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-flash-latest,gemini-flash-lite-latest").split(",")
    if m.strip()
]

RETRYABLE_CODES = {429, 500, 502, 503, 504}   # temporary problems
ATTEMPTS_PER_MODEL = 2
WAIT_SECONDS = 2

_client = None


class GeminiError(Exception):
    """Raised when Gemini is not configured or returns an unusable response."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _get_client() -> "genai.Client":
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key.startswith(("your_", "PASTE_")):
            raise GeminiError(
                "GEMINI_API_KEY is not set. Put your real key in the .env file and restart the server.",
                status_code=503,
            )
        _client = genai.Client(api_key=api_key.strip())
    return _client


def generate(prompt: str, system: str | None = None, json_mode: bool = False,
             temperature: float = 0.4) -> str:
    """Send a prompt to Gemini and return the response text."""
    config = types.GenerateContentConfig(
        system_instruction=system,
        temperature=temperature,
        response_mime_type="application/json" if json_mode else None,
    )

    models = [MODEL_NAME] + [m for m in FALLBACK_MODELS if m != MODEL_NAME]
    last_error = None

    for model in models:
        for attempt in range(ATTEMPTS_PER_MODEL):
            try:
                response = _get_client().models.generate_content(
                    model=model, contents=prompt, config=config
                )
            except GeminiError:
                raise
            except Exception as exc:
                last_error = exc
                code = getattr(exc, "code", None)
                if code in RETRYABLE_CODES:
                    if attempt < ATTEMPTS_PER_MODEL - 1:
                        time.sleep(WAIT_SECONDS * (attempt + 1))
                        continue          # try the same model once more
                    break                 # give up on this model, try the next
                if code == 404:
                    break                 # model not available, try the next
                raise GeminiError(f"Gemini request failed: {exc}") from exc

            text = (getattr(response, "text", None) or "").strip()
            if not text:
                raise GeminiError("Gemini returned an empty or blocked response. Try rephrasing.")
            return text

    raise GeminiError(
        "Gemini is busy right now (all models are overloaded or unavailable). "
        f"Please wait a minute and try again. Last error: {last_error}",
        status_code=503,
    )