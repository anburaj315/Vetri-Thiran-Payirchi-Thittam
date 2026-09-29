"""Offline tests: the Gemini call is mocked, so no API key or network is needed."""
import json
import os
import sys

os.environ["EXPLAIN_BACKEND"] = "gemini"          # don't load the local T5 model in tests
os.environ["GEMINI_API_KEY"] = "test-key"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient

import gemini_client
import main
import quiz_module

client = TestClient(main.app)

GOOD_QUIZ = [
    {"question": f"Q{i}?", "options": ["a", "b", "c", "d"], "answer": "b"} for i in range(1, 4)
]


@pytest.fixture
def fake_llm(monkeypatch):
    calls = []

    def _fake(prompt, system=None, json_mode=False, temperature=0.4):
        calls.append(prompt)
        if json_mode:
            return "```json\n" + json.dumps(GOOD_QUIZ) + "\n```"
        return "fake response"

    monkeypatch.setattr(gemini_client, "generate", _fake)
    return calls


def test_home_page_renders():
    r = client.get("/")
    assert r.status_code == 200
    assert "EduGenie" in r.text


def test_static_assets_served():
    assert client.get("/static/style.css").status_code == 200
    assert client.get("/static/app.js").status_code == 200


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_qa(fake_llm):
    r = client.get("/qa", params={"question": "Which is the largest ocean?"})
    assert r.status_code == 200 and r.json() == {"answer": "fake response"}


def test_qa_requires_question():
    assert client.get("/qa").status_code == 422


@pytest.mark.parametrize("path", ["/explain", "/explain/"])
def test_explain(fake_llm, path):
    r = client.post(path, json={"topic": "Photosynthesis"})
    assert r.status_code == 200
    assert r.json()["explanation"] == "fake response"


def test_explain_blank_topic_rejected(fake_llm):
    assert client.post("/explain", json={"topic": "   "}).status_code == 400


def test_summarize(fake_llm):
    r = client.post("/summarize/", json={"text": "Long text " * 20})
    assert r.status_code == 200 and r.json()["summary"] == "fake response"


def test_quiz_returns_three_valid_questions(fake_llm):
    r = client.post("/quiz", json={"text": "Pythagoras Theorem"})
    assert r.status_code == 200
    quiz = r.json()["quiz"]
    assert len(quiz) == 3
    for q in quiz:
        assert len(q["options"]) == 4 and q["answer"] in q["options"]


def test_learning_path(fake_llm):
    r = client.post("/learn/recommendations", json={"topic": "SQL"})
    assert r.status_code == 200 and r.json()["recommendations"] == "fake response"


def test_missing_api_key_gives_clear_error(monkeypatch):
    monkeypatch.setattr(gemini_client, "_client", None)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    r = client.get("/qa", params={"question": "hi"})
    assert r.status_code == 503 and "GEMINI_API_KEY" in r.json()["error"]


def test_bad_quiz_json_returns_error(monkeypatch):
    monkeypatch.setattr(gemini_client, "generate", lambda *a, **k: "not json at all")
    r = client.post("/quiz", json={"text": "x"})
    assert r.status_code == 502 and "Could not parse quiz" in r.json()["error"]


def test_clean_json_block():
    assert quiz_module.clean_json_block('```json\n[1]\n```') == "[1]"
    assert quiz_module.clean_json_block("[1]") == "[1]"


def test_quiz_letter_answer_is_normalised():
    items = [{"question": "q", "options": ["w", "x", "y", "z"], "answer": "C"}]
    assert quiz_module._validate(items)[0]["answer"] == "y"
