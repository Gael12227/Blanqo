import os, re, math
from typing import List, Tuple
from markdown_it import MarkdownIt
from sklearn.feature_extraction.text import TfidfVectorizer

STOP_HEADINGS = {"introduction", "summary", "references", "overview"}
md = MarkdownIt()

def read_markdown_texts(paths: List[str]) -> List[Tuple[str, str]]:
    docs = []
    for p in paths:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            docs.append((os.path.basename(p), f.read()))
    return docs

def chunk_fragments(name: str, text: str) -> List[str]:
    # split on headings & bullets; keep non-trivial chunks
    parts = re.split(r"(?m)^#{1,3}\s+.*$|^\s*[-*]\s+", text)
    return [t.strip() for t in parts if t and len(t.strip().split()) >= 8]

def extract_topics(texts: List[str], cap: int = 8) -> List[str]:
    # prefer H1/H2 headings; dedupe; stoplist
    headings = []
    for t in texts:
        for m in re.finditer(r"(?m)^(#{1,2})\s+(.+)$", t):
            title = re.sub(r"[^\w\s-]", "", m.group(2)).strip()
            if title and title.lower() not in STOP_HEADINGS:
                headings.append(title)
    # fallback: top tf-idf terms (multi-words) if not enough headings
    topics = []
    seen = set()
    for h in headings:
        k = h.lower()
        if k not in seen:
            topics.append(h)
            seen.add(k)
        if len(topics) >= cap:
            return topics
    if len(topics) < max(3, cap//2):
        vec = TfidfVectorizer(ngram_range=(1,2), stop_words="english", max_features=2000)
        X = vec.fit_transform(texts)
        means = X.mean(axis=0).A1
        vocab = vec.get_feature_names_out()
        pairs = sorted(zip(means, vocab), reverse=True)
        for _, term in pairs:
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
    vec = TfidfVectorizer(stop_words="english")
    X = vec.fit_transform(fragments + [topic])
    sims = (X[:-1] @ X[-1].T).toarray().ravel()
    idx = sims.argsort()[::-1][:top_k]
    return [fragments[i] for i in idx]