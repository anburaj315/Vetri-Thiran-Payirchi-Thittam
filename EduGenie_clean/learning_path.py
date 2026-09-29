"""Personalized learning path recommendations with Gemini."""
import gemini_client

SYSTEM = "You are an experienced curriculum designer and learning coach."


def get_learning_recommendations(topic: str, level: str = "beginner") -> str:
    prompt = f"""Create a structured learning path for: "{topic}".
The learner currently is at the "{level}" level.

Organize the plan from beginner to advanced. For each stage include:
- Stage name and approximate timeline (e.g. Week 1-2)
- Key concepts to learn
- Suggested resources (videos, articles, books, or courses)
- One small practice task

Finish with a short "Adaptive Learning Tips" section.
Use clear headings and bullet points."""
    return gemini_client.generate(prompt, system=SYSTEM, temperature=0.5)
