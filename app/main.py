import os, io, json
import re
from fastapi import FastAPI, Request, UploadFile, Form, File, Body, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
from datetime import datetime, date
from .parsers import read_docs
from . import llm

from .parsers import read_docs  
from .planner import chunk_fragments, extract_topics, plan_blocks, map_fragments_to_topic
from .qa import parse_bank, make_mcqs_from_fragments
from .models import Fragment, PlanBlock, Session, MCQ, Exam
from .storage import save_session, load_session, new_session_id, load_exams, save_exams, new_exam_id

app = FastAPI()
BASE = os.getcwd()
UPLOADS = os.path.join(BASE, "uploads")
os.makedirs(UPLOADS, exist_ok=True)

app.mount("/static", StaticFiles(directory=os.path.join(BASE, "app", "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE, "app", "templates"))

def _save_upload(file: UploadFile, subdir=""):
    d = os.path.join(UPLOADS, subdir)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, file.filename)
    with open(path, "wb") as f:
        f.write(file.file.read())
    return path

def _save_upload_sync(file: UploadFile, subdir=""):
    """Use this only when you've already read() the file content."""
    import os
    d = os.path.join(UPLOADS, subdir)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, file.filename)
    return path

async def _read_and_save(file: UploadFile, subdir=""):
    import os
    d = os.path.join(UPLOADS, subdir)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, file.filename)
    content = await file.read()           # <-- async safe
    with open(path, "wb") as f:
        f.write(content)
    return path

def slugify(s: str) -> str:
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    s = re.sub(r"[\s_-]+", "-", s)
    return s or "session"

def list_session_files():
    sess_dir = os.path.join(UPLOADS, "sessions")
    if not os.path.isdir(sess_dir):
        return []
    return [os.path.join(sess_dir, f) for f in os.listdir(sess_dir) if f.endswith(".json")]

@app.get("/", response_class=HTMLResponse)
def home(req: Request):
    # sessions
    recent = []
    for path in sorted(list_session_files(), reverse=True)[:20]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            try:
                data = json.load(f)
                recent.append({
                    "id": data["id"],
                    "name": data.get("name", data["id"]),
                    "created_at": data.get("created_at", "")
                })
            except Exception:
                pass

    # exams
    exams = load_exams()
    # sort by date ascending; only future 90 days for "upcoming"
    def _parse(d):
        try: return datetime.strptime(d, "%Y-%m-%d").date()
        except: return date.max
    today = date.today()
    upcoming = sorted(
        [e for e in exams if _parse(e.get("date","")) >= today],
        key=lambda e: _parse(e.get("date",""))
    )

    return templates.TemplateResponse("home.html", {
        "request": req,
        "recent": recent,
        "upcoming_exams": upcoming
    })

@app.post("/start")
async def start(
    req: Request,
    session_name: str = Form(...),                      # <-- NEW
    minutes: int = Form(30),                            # <-- moved here
    notes: List[UploadFile] = File(...),
    syllabus: UploadFile | None = File(None),
    question_bank: UploadFile | None = File(None),
):
    # unique name (case-insensitive)
    name_clean = session_name.strip()
    if not name_clean:
        raise HTTPException(400, "Session name is required.")

    existing_names = set()
    for path in list_session_files():
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing_names.add((json.load(f).get("name","") or "").lower())
        except Exception:
            pass
    if name_clean.lower() in existing_names:
        raise HTTPException(400, "Session name must be unique. Pick a different name.")

    # persist uploads, build plan (unchanged except we set Session.name below)
    note_paths = [await _read_and_save(f, "notes") for f in notes if f and f.filename]
    if not note_paths:
        return PlainTextResponse("No notes were uploaded. Please add at least one .md file.", status_code=400)

    docs = read_docs(note_paths)
    all_texts = [t for _, t in docs]
    if not any((t or "").strip() for t in all_texts):
        return PlainTextResponse("Uploaded notes appear empty or unreadable. Please upload valid .md files.", status_code=400)
    
    topics = extract_topics(all_texts, cap=8) or ["Session Overview"]


    frags = []
    for name, text in docs:
        for ch in chunk_fragments(name, text):
            frags.append(Fragment(doc_id=name, text=ch))

    topics = extract_topics(all_texts, cap=8) or ["Session Overview"]
    if not frags and all_texts:
        frags = [Fragment(doc_id="notes", text=all_texts[0])]
    blocks_raw = plan_blocks(topics, total_minutes=minutes)

    # syllabus (unchanged)
    syllabus_topics = []
    if syllabus and syllabus.filename:
        spath = await _read_and_save(syllabus, "syllabus")
        with open(spath, "r", encoding="utf-8", errors="ignore") as f:
            syllabus_topics = [ln.strip("-* \n\r\t") for ln in f if ln.strip()]

    # question bank (unchanged)
    bank = {}
    if question_bank and question_bank.filename:
        qpath = await _read_and_save(question_bank, "bank")
        with open(qpath, "r", encoding="utf-8", errors="ignore") as f:
            bank = parse_bank(f.read())

    # map fragments per block
    blocks = []
    frag_texts = [f.text for f in frags]
    for b in blocks_raw:
        top_frags = map_fragments_to_topic(frag_texts, b["title"])[:6] if frag_texts else []
        blocks.append(PlanBlock(id=b["id"], title=b["title"], minutes=b["minutes"],
                                fragments=[Fragment(doc_id="notes", text=t) for t in top_frags]))

    session = Session(
        id=new_session_id(),
        name=name_clean,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        blocks=blocks,
        syllabus_topics=syllabus_topics,
        pins=[])
    save_session(session)

    resp = RedirectResponse(url=f"/session/{session.id}", status_code=303)
    resp.set_cookie("bank", json.dumps(bank))
    return resp

@app.post("/session/{sid}/delete")
def delete_session(sid: str):
    path = os.path.join(UPLOADS, "sessions", f"{sid}.json")
    if os.path.isfile(path):
        os.remove(path)
    # back to home
    return RedirectResponse(url="/", status_code=303)

@app.get("/session/{sid}", response_class=HTMLResponse)
def session_view(req: Request, sid: str):
    sess = load_session(sid)
    total_minutes = sum(b.minutes for b in sess.blocks) or 0
    return templates.TemplateResponse("session.html", {
        "request": req, "sid": sid, "sess": sess,
        "total_minutes": total_minutes
    })

@app.post("/session/{sid}/toggle-covered/{bid}")
def toggle_covered(sid: str, bid: str):
    sess = load_session(sid)
    for b in sess.blocks:
        if b.id == bid:
            b.covered = not b.covered
            break
    save_session(sess)
    return RedirectResponse(url=f"/session/{sid}", status_code=303)

@app.post("/session/{sid}/pin")
async def pin_fragment(sid: str, text: str = Form(...)):
    sess = load_session(sid)
    i = next((i for i,p in enumerate(sess.pins) if p.text == text), None)
    if i is not None:
        sess.pins.pop(i)  # unpin
    else:
        if not any(p.text == text for p in sess.pins):
            sess.pins = ([Fragment(doc_id="notes", text=text)] + sess.pins)[:3]
    save_session(sess)
    return RedirectResponse(url=f"/session/{sid}", status_code=303)


@app.post("/session/{sid}/mcq/{bid}", response_class=HTMLResponse)
async def generate_mcq(req: Request, sid: str, bid: str):
    sess = load_session(sid)
    bank = {}
    try:
        bank = json.loads(req.cookies.get("bank","{}"))
    except: pass
    blk = next(b for b in sess.blocks if b.id == bid)
    mcqs = make_mcqs_from_fragments(blk.title, [f.text for f in blk.fragments], bank)
    return PlainTextResponse(json.dumps(mcqs, ensure_ascii=False, indent=2), media_type="application/json")

@app.post("/session/{sid}/mcq_asked/{bid}")
async def mcq_asked(sid: str, bid: str, payload: dict = Body(...)):
    sess = load_session(sid)
    blk = next(b for b in sess.blocks if b.id == bid)
    q = payload.get("question","")
    if q and not any(m.question == q for m in blk.asked_mcqs):
        blk.asked_mcqs.append(MCQ(
            question=q,
            options=payload.get("options",[])[:6],
            answer=payload.get("answer","")
        ))
        save_session(sess)
    return PlainTextResponse("OK")

@app.post("/session/{sid}/duration")
async def update_duration(sid: str, minutes: int = Form(...)):
    sess = load_session(sid)
    old_sum = sum(b.minutes for b in sess.blocks) or 1
    scale = max(10, minutes) / old_sum
    for b in sess.blocks:
        b.minutes = max(3, int(round(b.minutes * scale)))
    save_session(sess)
    return RedirectResponse(url=f"/session/{sid}", status_code=303)

@app.post("/exams/add")
def add_exam(title: str = Form(...), date_str: str = Form(...), topics: str = Form("")):
    exams = load_exams()
    eid = new_exam_id()
    topic_list = [t.strip() for t in topics.split(",") if t.strip()]
    exams.append({"id": eid, "title": title.strip(), "date": date_str.strip(), "topics": topic_list})
    save_exams(exams)
    return RedirectResponse(url="/", status_code=303)

@app.post("/exams/delete/{eid}")
def delete_exam(eid: str):
    exams = load_exams()
    exams = [e for e in exams if e.get("id") != eid]
    save_exams(exams)
    return RedirectResponse(url="/", status_code=303)

def order_by_syllabus(topics: List[str], syllabus_topics: List[str]) -> List[str]:
    """Return topics ordered by syllabus first (in given order), then leftovers."""
    if not syllabus_topics:
        return topics
    lower_map = {t.lower(): t for t in topics}
    ordered = []
    seen = set()
    # syllabus order (case-insensitive matches to extracted topics)
    for s in syllabus_topics:
        k = s.strip().lower()
        if k in lower_map and k not in seen:
            ordered.append(lower_map[k])
            seen.add(k)
    # leftovers
    for t in topics:
        if t not in seen:
            ordered.append(t)
    return ordered

def boost_nearest_exam_topics(topics: List[str], exams: List[dict]) -> List[str]:
    """Bring nearest exam topics to the front (keeping syllabus ordering within that subset)."""
    if not exams:
        return topics
    # choose nearest upcoming exam
    today = date.today()
    def _parse(d):
        try: return datetime.strptime(d, "%Y-%m-%d").date()
        except: return None
    future = [(e, _parse(e.get("date",""))) for e in exams]
    future = [x for x in future if x[1] and x[1] >= today]
    if not future:
        return topics
    nearest = sorted(future, key=lambda x: x[1])[0][0]
    focus = [t.strip().lower() for t in nearest.get("topics", []) if t.strip()]
    if not focus:
        return topics

    in_focus = []
    others = []
    for t in topics:
        (in_focus if t.lower() in focus else others).append(t)
    return in_focus + others

def allocate_minutes_with_focus(blocks_raw: List[dict], focus_topics: List[str], total_minutes: int) -> List[dict]:
    """Give +40% budget to focus topics, normalize total to requested minutes."""
    if not blocks_raw:
        return blocks_raw
    base = 1.0
    boost = 1.4
    weights = []
    for b in blocks_raw:
        w = boost if b["title"].lower() in [ft.lower() for ft in focus_topics] else base
        weights.append(w)
    s = sum(weights) or 1.0
    per_unit = total_minutes / s
    out = []
    for i, b in enumerate(blocks_raw):
        mins = max(3, int(round(weights[i] * per_unit)))
        out.append({"id": b["id"], "title": b["title"], "minutes": mins})
    # tiny final normalization to hit the exact total
    diff = total_minutes - sum(x["minutes"] for x in out)
    if diff != 0:
        # adjust the first block (or last) by the diff
        idx = 0 if diff > 0 else -1
        out[idx]["minutes"] = max(3, out[idx]["minutes"] + diff)
    return out

@app.get("/session/{sid}/export")
def export_session(sid: str):
    sess = load_session(sid)
    lines = [f"# Session: {sess.name} ({sid})", ""]

    lines += ["## Covered", ""]
    for b in sess.blocks:
        if b.covered:
            lines.append(f"- {b.title} ({b.minutes}m)")

    lines += ["", "## Missed / Next Up", ""]
    for b in sess.blocks:
        if not b.covered:
            lines.append(f"- {b.title} ({b.minutes}m)")

    lines += ["", "## Pinned", ""]
    for p in sess.pins:
        lines.append(f"> {p.text}")

    any_mcq = any(b.asked_mcqs for b in sess.blocks)
    if any_mcq:
        lines += ["", "## MCQs Asked (by topic)", ""]
        for b in sess.blocks:
            if b.asked_mcqs:
                lines.append(f"### {b.title}")
                for i, q in enumerate(b.asked_mcqs, 1):
                    lines.append(f"{i}. {q.question}")
                    for j, opt in enumerate(q.options):
                        letter = chr(65 + j)
                        lines.append(f"   {letter}. {opt}")
                    # keep answer in export only
                    lines.append(f"   **Answer:** {q.answer}")
                    lines.append("")

    md = "\n".join(lines)
    return PlainTextResponse(md, media_type="text/markdown")