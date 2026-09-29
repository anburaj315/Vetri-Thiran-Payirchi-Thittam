# EduGenie – Google Gemini Powered Learning Assistant

Ask questions, get simple explanations, generate quizzes, summarize text and get
personalized learning paths. Built with **FastAPI** + a plain **HTML/CSS/JS** frontend.

| Feature | Endpoint | Model |
|---|---|---|
| Q&A | `GET /qa?question=...` | Gemini |
| Explain a concept | `POST /explain` `{"topic": "..."}` | LaMini-Flan-T5-783M (local), falls back to Gemini |
| Quiz (3 MCQs × 4 options) | `POST /quiz` `{"text": "..."}` | Gemini |
| Summarize | `POST /summarize` `{"text": "..."}` | Gemini |
| Learning path | `POST /learn/recommendations` `{"topic": "...", "level": "beginner"}` | Gemini |

## Project structure
```
EduGenie/
├── main.py                 # FastAPI app + routes
├── gemini_client.py        # shared Gemini client (reads .env)
├── explanation_module.py   # local LaMini-Flan-T5 (Gemini fallback)
├── qna.py                  # question answering
├── quiz_module.py          # quiz generation + JSON cleaning/validation
├── summary_module.py       # summarization
├── learning_path.py        # learning recommendations
├── templates/index.html    # frontend page
├── static/style.css        # styling
├── static/app.js           # frontend logic
├── tests/test_app.py       # offline tests (Gemini mocked)
├── requirements.txt
├── requirements-dev.txt
├── .env.example            # copy to .env
└── .vscode/                # launch + test settings
```

## 1. Prerequisites
* **Python 3.10+** (`python --version`; on Windows tick "Add Python to PATH" when installing)
* **VS Code** with the *Python* extension
* A free **Gemini API key** from https://aistudio.google.com/apikey

## 2. Setup in VS Code
1. **File → Open Folder…** and choose the `EduGenie` folder.
2. Open the terminal: **Terminal → New Terminal**.
3. Create and activate a virtual environment:
   * Windows (PowerShell): `python -m venv venv` then `venv\Scripts\Activate.ps1`
     (if blocked: `Set-ExecutionPolicy -Scope Process RemoteSigned`)
   * macOS / Linux (incl. Mac M1): `python3 -m venv venv` then `source venv/bin/activate`
4. In VS Code press **Ctrl/Cmd+Shift+P → "Python: Select Interpreter"** and pick the `venv` one.
5. Install dependencies: `pip install -r requirements-dev.txt`
   (this includes PyTorch + Transformers for the local model, which is a large download).
6. Create your config file:
   * Windows: `copy .env.example .env`   · macOS/Linux: `cp .env.example .env`
   * Open `.env` and paste your key: `GEMINI_API_KEY=...`

> **Want a light install (no ~3 GB model)?** Set `EXPLAIN_BACKEND=gemini` in `.env`
> and remove `transformers`, `torch`, `sentencepiece` from `requirements.txt` before installing.
> If the local model can't load for any reason, EduGenie automatically falls back to Gemini.

## 3. Run
```
uvicorn main:app --reload
```
Open **http://127.0.0.1:8000**. (Or press **F5** in VS Code and choose "EduGenie (FastAPI)".)
Interactive API docs: http://127.0.0.1:8000/docs

The first "Explain" request with the local backend downloads LaMini-Flan-T5 once
(a few minutes); later requests are fast.

## 4. Test
**Automated (no API key or internet needed):**
```
pytest -v
```
**Manual, in the browser** (pick a task from the dropdown):
1. *Q&A* → `Which is the largest ocean?`
2. *Explain* → `Photosynthesis`
3. *Quiz* → `Pythagoras Theorem` – you get 3 questions; pick answers to see ✅/❌ and your score
4. *Summarize* → paste any long paragraph
5. *Learning Path* → `SQL`

**Manual, via curl:**
```
curl "http://127.0.0.1:8000/qa?question=Which%20is%20the%20largest%20ocean%3F"
curl -X POST http://127.0.0.1:8000/quiz -H "Content-Type: application/json" -d "{\"text\":\"Pythagoras Theorem\"}"
curl http://127.0.0.1:8000/health
```

## Troubleshooting
| Problem | Fix |
|---|---|
| `GEMINI_API_KEY is not set` | Create `.env` from `.env.example` and restart uvicorn |
| `Gemini request failed: ... model ... not found` | Set `GEMINI_MODEL` in `.env` to a current model (https://ai.google.dev/gemini-api/docs/models) |
| `429` / quota errors | Free-tier rate limit – wait a minute and retry |
| `uvicorn` not found | Activate the venv, or run `python -m uvicorn main:app --reload` |
| Port 8000 busy | `uvicorn main:app --reload --port 8001` |
| Torch install fails / too big | Use `EXPLAIN_BACKEND=gemini` (see light install above) |
