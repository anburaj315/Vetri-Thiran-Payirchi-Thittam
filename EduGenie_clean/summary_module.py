"""Summarization with Gemini."""
import gemini_client

SYSTEM = (
    "You are an expert study assistant who summarizes educational text."
)


def summarize_text(text: str) -> str:
    prompt = f"""Summarize the following passage for a student doing quick revision.
- Keep all core facts and key terms.
- Remove redundancy.
- Use 3-6 short bullet points, followed by a one-line takeaway.

Passage:
{text}
"""
    return gemini_client.generate(prompt, system=SYSTEM)
