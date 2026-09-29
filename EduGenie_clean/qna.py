"""Question answering with Gemini."""
import gemini_client

SYSTEM = (
    "You are EduGenie, a friendly and accurate tutor. Answer the student's question "
    "clearly and concisely (2-5 sentences unless more detail is truly needed). "
    "If you are unsure, say so instead of guessing."
)


def answer_question_with_gemini(question: str) -> str:
    return gemini_client.generate(f"Question: {question}", system=SYSTEM)
