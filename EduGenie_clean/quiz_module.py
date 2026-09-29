"""Quiz generation: 3 MCQs with 4 options each, returned as validated JSON."""
import json
import re

import gemini_client

NUM_QUESTIONS = 3
NUM_OPTIONS = 4


def clean_json_block(text: str) -> str:
    """Remove Markdown ```json code fences that models sometimes add."""
    match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    return (match.group(1) if match else text).strip()


def _validate(items) -> list:
    if isinstance(items, dict):  # tolerate {"questions": [...]}
        items = items.get("questions", [])
    if not isinstance(items, list) or not items:
        raise ValueError("Model did not return a list of questions.")

    quiz = []
    for i, item in enumerate(items[:NUM_QUESTIONS], start=1):
        question = str(item.get("question", "")).strip()
        options = [str(o).strip() for o in item.get("options", [])]
        answer = str(item.get("answer", "")).strip()
        if not question or len(options) != NUM_OPTIONS:
            raise ValueError(f"Question {i} is malformed (needs a question and {NUM_OPTIONS} options).")
        if answer not in options:
            # accept "A"/"B"/"C"/"D" or a case-insensitive match
            letters = "ABCD"
            if answer[:1].upper() in letters and len(answer) <= 2:
                answer = options[letters.index(answer[:1].upper())]
            else:
                lowered = {o.lower(): o for o in options}
                if answer.lower() in lowered:
                    answer = lowered[answer.lower()]
                else:
                    raise ValueError(f"Question {i}: the answer does not match any option.")
        quiz.append({"question": question, "options": options, "answer": answer})
    return quiz


def generate_quiz(text: str) -> list:
    """Return a list of {'question', 'options', 'answer'} dicts.

    Raises ValueError (with a debugging message) if the model output is unusable.
    """
    prompt = f"""You are a quiz generator.

From the following topic or passage, create {NUM_QUESTIONS} multiple-choice questions. Each question must include:
- A "question"
- A list of {NUM_OPTIONS} "options" (one correct, three plausible distractors)
- A correct "answer" that must exactly match one of the options.

Return ONLY valid JSON (no commentary, no Markdown), like this:
[
  {{
    "question": "What is ...?",
    "options": ["A", "B", "C", "D"],
    "answer": "A"
  }}
]

Topic or passage:
{text}
"""
    raw = gemini_client.generate(prompt, json_mode=True, temperature=0.6)
    cleaned = clean_json_block(raw)
    try:
        return _validate(json.loads(cleaned))
    except (json.JSONDecodeError, ValueError, AttributeError, TypeError) as exc:
        raise ValueError(f"Could not parse quiz from model output: {exc}. Raw output: {raw[:300]}") from exc
