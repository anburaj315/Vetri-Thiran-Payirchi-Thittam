"""Concept explanation.

Primary backend: the local, CPU-friendly LaMini-Flan-T5-783M model (Hugging Face).
Fallback (or when EXPLAIN_BACKEND=gemini): Gemini.
"""
import logging
import os
import threading

import gemini_client

logger = logging.getLogger("edugenie.explain")

LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "MBZUAI/LaMini-Flan-T5-783M")
EXPLAIN_BACKEND = os.getenv("EXPLAIN_BACKEND", "local").lower()

_pipeline = None
_pipeline_failed = False
_lock = threading.Lock()


def _load_pipeline():
    """Load the local model once (lazy, thread-safe). Returns None if unavailable."""
    global _pipeline, _pipeline_failed
    if _pipeline is not None or _pipeline_failed:
        return _pipeline
    with _lock:
        if _pipeline is not None or _pipeline_failed:
            return _pipeline
        try:
            from transformers import pipeline  # imported lazily: slow to import

            logger.info("Loading local model %s (first run downloads it)...", LOCAL_MODEL_NAME)
            _pipeline = pipeline("text2text-generation", model=LOCAL_MODEL_NAME)
        except Exception as exc:
            logger.warning("Local model unavailable (%s). Falling back to Gemini.", exc)
            _pipeline_failed = True
    return _pipeline


def _explain_local(topic: str) -> str | None:
    pipe = _load_pipeline()
    if pipe is None:
        return None
    prompt = (
        f"Explain the concept of '{topic}' in simple words that a beginner or school "
        f"student can understand. Use short sentences and a small example."
    )
    out = pipe(prompt, max_new_tokens=256, do_sample=False, repetition_penalty=1.2)
    text = (out[0]["generated_text"] or "").strip()
    return text or None


def _explain_gemini(topic: str) -> str:
    prompt = (
        f"Explain '{topic}' in simple language for a beginner. Use short sentences, "
        f"one everyday analogy, and a tiny example. Keep it under 150 words."
    )
    return gemini_client.generate(prompt, system="You are a patient teacher.")


def explain_topic(topic: str) -> str:
    if EXPLAIN_BACKEND != "gemini":
        try:
            result = _explain_local(topic)
            if result:
                return result
        except Exception as exc:
            logger.warning("Local generation failed (%s). Falling back to Gemini.", exc)
    return _explain_gemini(topic)
