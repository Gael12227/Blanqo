import os, json
from typing import List, Dict, Any

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

def _client():
    key = os.getenv("OPENAI_API_KEY", "")
    if not key or OpenAI is None:
        return None
    return OpenAI()

def available() -> bool:
    return _client() is not None

# --- helpers
SYSTEM_JSON = {"role": "system", "content": "Return only valid JSON. No prose."}

def _chat_json(prompt: str, model: str = "gpt-4o-mini") -> Any:
    cli = _client()
    if cli is None:
        return None
    resp = cli.chat.completions.create(
        model=model,
        messages=[SYSTEM_JSON, {"role":"user","content":prompt}],
        temperature=0.2,
    )
    content = resp.choices[0].message.content
    try:
        return json.loads(content)
    except Exception:
        # best-effort: strip code fences
        content = content.strip().strip("```").replace("json", "", 1)
        return json.loads(content)

# --- public APIs
def refine_plan(topics: List[str], minutes: int) -> List[Dict]:
    """
    Returns list[ {title, minutes, objective} ]
    """
    prompt = f"""
    Topics: {topics}
    Total minutes: {minutes}
    Task: Propose a concise teaching plan with 4–8 blocks.
    Output JSON: [{{"title": "...", "minutes": int, "objective": "..."}}]
    Make sure total minutes ≈ {minutes}.
    """
    return _chat_json(prompt)

def mcqs_from_notes(topic: str, fragments: List[str], n: int = 4) -> List[Dict]:
    """
    Returns list[ {question, options, answer} ]
    """
    joined = "\n\n".join(fragments[:6])
    prompt = f"""
    Topic: {topic}
    Notes:
    {joined}

    Make {n} high-quality MCQs. Options A–D. One correct answer.
    Output JSON: [{{"question": "...", "options": ["A","B","C","D"], "answer": "..."}}]
    """
    return _chat_json(prompt)

def missed_topics(syllabus: List[str], covered: List[str]) -> List[Dict]:
    """
    Returns list[ {topic, why} ] for top 3 uncovered.
    """
    prompt = f"""
    Syllabus topics: {syllabus}
    Already covered: {covered}
    Return top 3 important uncovered items with a short 'why it matters'.
    Output JSON: [{{"topic": "...", "why": "..."}}]
    """
    return _chat_json(prompt)
