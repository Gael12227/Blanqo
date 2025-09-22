import json, os, uuid
from typing import Dict
from .models import Session

DATA_DIR = os.path.join(os.getcwd(), "uploads")
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

BASE = os.getcwd()
UPLOADS = os.path.join(BASE, "uploads")
os.makedirs(UPLOADS, exist_ok=True)

def _exams_path():
    os.makedirs(UPLOADS, exist_ok=True)
    return os.path.join(UPLOADS, "exams.json")

def load_exams():
    p = _exams_path()
    if not os.path.isfile(p):
        return []
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        try:
            return json.load(f)
        except Exception:
            return []

def save_exams(exams):
    p = _exams_path()
    with open(p, "w", encoding="utf-8") as f:
        json.dump(exams, f, ensure_ascii=False, indent=2)

def new_exam_id():
    return uuid.uuid4().hex[:12]

def save_session(sess: Session):
    path = os.path.join(SESSIONS_DIR, f"{sess.id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sess.dict(), f, ensure_ascii=False, indent=2)

def load_session(session_id: str) -> Session:
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Session(**data)

def new_session_id() -> str:
    return uuid.uuid4().hex[:12]