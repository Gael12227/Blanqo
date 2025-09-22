import os, re
from typing import Iterable, List, Tuple
from scipy.sparse import vstack
from markdown_it import MarkdownIt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

STOP_HEADINGS = {"introduction", "summary", "references", "overview", "table of contents", "toc", "agenda"}
md = MarkdownIt()

# Regex helpers
_CODE_FENCE_RE = re.compile(r"```.*?```", re.S)
_INLINE_CODE_RE = re.compile(r"`[^`]+`")
_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_WS_RE = re.compile(r"\s+")
# bullets: -, *, •, +, or 1. / 1) / (1)
_BULLET_RE = re.compile(r"^\s*(?:[-*•+]\s+|\(?\d{1,3}[.)]\s+)")
# sentence-ish boundaries (cheap + effective)
_SENT_BOUND_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z(0-9])")

STOPLINES = set([
    "table of contents", "toc", "agenda", "references", "bibliography"
])

def read_markdown_texts(paths: List[str]) -> List[Tuple[str, str]]:
    docs = []
    for p in paths:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            docs.append((os.path.basename(p), f.read()))
    return docs

def _clean_text(t: str) -> str:
    t = _CODE_FENCE_RE.sub(" ", t)
    t = _INLINE_CODE_RE.sub(" ", t)
    t = _URL_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t)
    return t.strip()

def _normalize_sentence(s: str) -> str:
    s = s.strip(" -•\t")
    if not s:
        return ""
    # sentence case for first char
    if s and s[0].islower():
        s = s[0].upper() + s[1:]
    # ensure terminal punctuation
    if s and s[-1] not in ".!?":
        s += "."
    return s

def _extract_raw_points(lines: List[str]) -> List[str]:
    points: List[str] = []
    buf: List[str] = []

    def flush_buf():
        if not buf:
            return
        para = " ".join(buf).strip()
        buf.clear()
        if not para:
            return
        # split para into sentences
        for sent in _SENT_BOUND_RE.split(para):
            sent = sent.strip()
            if len(sent) >= 8:
                points.append(sent)

    for ln in lines:
        l = ln.strip()
        if not l:  # paragraph break
            flush_buf()
            continue
        if l.lower() in STOPLINES:
            flush_buf()
            continue
        # explicit bullet → take as one point
        if _BULLET_RE.match(l):
            flush_buf()
            l2 = _BULLET_RE.sub("", l).strip()
            if l2:
                points.append(l2)
            continue
        # accumulate paragraph text
        buf.append(l)

    flush_buf()
    return points

def _dedupe_semantic(points: List[str], threshold: float = 0.72, cap: int = 80) -> List[str]:
    # normalize + length guard
    cleaned = []
    for p in points:
        p = _normalize_sentence(_clean_text(p))
        if 8 <= len(p) <= 220:
            cleaned.append(p)

    # exact de-dupe
    seen = set()
    dedup = []
    for p in cleaned:
        key = p.lower()
        if key in seen:
            continue
        seen.add(key)
        dedup.append(p)

    if len(dedup) <= 1:
        return dedup[:cap]

    # TF-IDF encode all
    vec = TfidfVectorizer(min_df=1, ngram_range=(1, 2))
    X = vec.fit_transform(dedup)

    keep: List[str] = []
    kept_rows = []  # store sparse rows (csr_matrix)

    for i, p in enumerate(dedup):
        if not kept_rows:
            keep.append(p)
            kept_rows.append(X[i])
            continue

        # stack kept rows into a single sparse matrix
        K = vstack(kept_rows)
        # cosine similarity between current row and all kept rows
        sims = cosine_similarity(X[i], K).ravel()

        if sims.max(initial=0.0) < threshold:
            keep.append(p)
            kept_rows.append(X[i])

        if len(keep) >= cap:
            break

    return keep


def chunk_fragments(doc_name: str, full_text: str) -> Iterable[str]:

    if not full_text or not full_text.strip():
        return []
    # Light cleanup & line-based pass
    text = _clean_text(full_text)
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    raw_points = _extract_raw_points(lines)
    points = _dedupe_semantic(raw_points, threshold=0.72, cap=80)
    return points

def extract_topics(texts: List[str], cap: int = 8) -> List[str]:
    """Prefer H1/H2 headings; dedupe; stoplist. Falls back to TF-IDF bigrams."""
    headings = []
    for t in texts:
        # H1 / H2 (works for Markdown and our PPTX '# Slide N' injection)
        for m in re.finditer(r"(?m)^(#{1,2})\s+(.+)$", t):
            title = re.sub(r"[^\w\s-]", "", m.group(2)).strip()
            if title and title.lower() not in STOP_HEADINGS:
                headings.append(title)

    topics = []
    seen = set()
    for h in headings:
        k = h.lower()
        if k not in seen:
            topics.append(h)
            seen.add(k)
        if len(topics) >= cap:
            return topics

    if len(topics) < max(3, cap // 2):
        vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=2000)
        X = vec.fit_transform(texts)
        means = X.mean(axis=0).A1
        vocab = vec.get_feature_names_out()
        pairs = sorted(zip(means, vocab), reverse=True)
        for _, term in pairs:
            # prefer bigrams as pseudo-topics
            if term.count(" ") == 1 and term not in STOP_HEADINGS:
                if term.lower() not in seen:
                    topics.append(term.title())
                    seen.add(term.lower())
                if len(topics) >= cap:
                    break
    return topics[:cap]

def plan_blocks(topics: List[str], total_minutes: int = 30):
    k = len(topics) or 1
    base = max(4, total_minutes // k)
    blocks = []
    for i, t in enumerate(topics):
        minutes = base * (2 if i == 0 and k > 1 else 1)  # give first topic more time
        blocks.append({"id": f"b{i+1}", "title": t, "minutes": minutes})
    # normalize to total_minutes
    s = sum(b["minutes"] for b in blocks)
    if s > 0:
        scale = total_minutes / s
        for b in blocks:
            b["minutes"] = max(3, int(round(b["minutes"] * scale)))
    return blocks

def map_fragments_to_topic(fragments: List[str], topic: str, top_k=3):
    if not fragments:
        return []
    vec = TfidfVectorizer(stop_words="english")
    X = vec.fit_transform(fragments + [topic])
    sims = (X[:-1] @ X[-1].T).toarray().ravel()
    idx = sims.argsort()[::-1][:top_k]
    return [fragments[i] for i in idx]
