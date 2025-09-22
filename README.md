# BrainStormer (Minimal Starter)

A projector-friendly teaching whiteboard powered mostly by your uploaded notes.
This minimal version uses **TF‑IDF** (no embeddings) to:
- Parse your notes (Markdown/TXT),
- Propose a simple lesson plan,
- Line up note fragments for each topic,
- Generate basic practice questions from your notes,
- Show a "Next Up" sidebar you can reorder.

> Upgrade paths (later): PDF parsing, embeddings (sentence-transformers), and web search assist.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

## How it works
- Upload one or more `.md` or `.txt` note files on the home page.
- Enter session duration and intent.
- The app extracts headings/keywords, creates a simple plan, and shows:
  - Main stage: current topic's key fragments
  - Sidebar: Next Up topics (click to jump)
  - Practice: generate MCQs from the current topic

All data is saved as JSON in `data/` and files in `uploads/`.

## Project Structure
```
app/
  main.py           # FastAPI app + routes
  planner.py        # Note parsing, TF-IDF, plan generator
  qa.py             # Simple MCQ generator from notes
  templates/        # Jinja2 templates (HTML)
  static/style.css  # Projector-friendly CSS
uploads/            # Uploaded notes
data/               # Saved sessions as JSON
```

## Notes
- This is a minimal educational scaffold. It avoids DBs and heavy ML.
- To upgrade:
  - Replace TF-IDF with sentence-transformers embeddings (FAISS).
  - Add PDF parsing via `pymupdf`.
  - Add WebSockets for live updates.
  - Add web search assist behind a feature flag.
```

