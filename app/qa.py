import random, re
from typing import List, Dict
from . import llm

def parse_bank(text: str) -> Dict[str, List[Dict]]:
    """
    # Topic: Elasticity
    - Q: What is price elasticity of demand?
      A: The responsiveness of quantity demanded to price change.
    """
    bank = {}
    current = None
    for line in text.splitlines():
        if line.startswith("# Topic:"):
            current = line.split(":",1)[1].strip()
            bank[current] = []
        elif line.strip().startswith("- Q:") and current:
            q = line.split("Q:",1)[1].strip()
            bank[current].append({"q": q, "a": ""})
        elif line.strip().startswith("A:") and current and bank[current]:
            bank[current][-1]["a"] = line.split("A:",1)[1].strip()
    return bank

def mcqize(q: str, a: str):
    opts = list({a, "None of the above", "All of the above", "It depends", "A constant value"})
    random.shuffle(opts)
    opts = opts[:4]
    if a not in opts:
        opts[random.randrange(len(opts))] = a
    return {"question": q, "options": opts, "answer": a}

def make_mcqs_from_fragments(topic: str, frags: List[str], bank: Dict[str, List[Dict]], n=4):
    # 0) Prefer uploaded bank
    made = []
    for it in bank.get(topic, []):
        made.append(mcqize(it["q"], it["a"]))
        if len(made) >= n: return made

    # 1) LLM path (if available)
    if llm.available():
        try:
            res = llm.mcqs_from_notes(topic, frags, n=n) or []
            valid = []
            for q in res:
                if isinstance(q, dict) and q.get("question") and q.get("options") and q.get("answer"):
                    # normalize to exactly 4 options if possible
                    opts = list(q["options"])[:4] if isinstance(q["options"], list) else []
                    if len(opts) < 4:
                        # pad with dummy distractors
                        while len(opts) < 4:
                            opts.append(f"Option {len(opts)+1}")
                    valid.append({"question": q["question"], "options": opts, "answer": q["answer"]})
                if len(valid) >= n: break
            if valid:
                return valid[:n]
        except Exception:
            pass
    # Fallback from text
    sentences = []
    for f in frags:
        sentences += re.split(r"(?<=[.!?])\s+", f)
    sentences = [s for s in sentences if 8 <= len(s.split()) <= 30]
    for s in sentences:
        # crude cloze
        words = s.split()
        key = words[0].strip(",.").capitalize()
        blanked = s.replace(words[0], "_____")
        made.append(mcqize(f"What does _____ refer to here? {blanked}", key))
        if len(made) >= n: break
    # ensure at least T/F
    while len(made) < n:
        made.append({"question": f"{topic}: True or False — definition examples are helpful.",
                     "options": ["True","False"], "answer": "True"})
    return made
