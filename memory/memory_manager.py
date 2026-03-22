import json
import os
from datetime import datetime, timezone

MEMORY_PATH = os.getenv("MEMORY_PATH", "memory/memory.json")


def load_memory() -> dict:
    if os.path.exists(MEMORY_PATH):
        with open(MEMORY_PATH) as f:
            return json.load(f)
    return {"facts": {}, "keyword_bank": {}, "bibles": {}}


def save_memory(memory: dict):
    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
    with open(MEMORY_PATH, "w") as f:
        json.dump(memory, f, indent=2)


def add_keyword(memory: dict, term: str, initial_score: int = 50):
    bank = memory.setdefault("keyword_bank", {})
    if term not in bank:
        bank[term] = {
            "term": term,
            "score": initial_score,
            "last_hit": datetime.now(timezone.utc).isoformat(),
            "hit_count": 1
        }


def hit_keyword(memory: dict, term: str, boost: int = 5):
    bank = memory.setdefault("keyword_bank", {})
    if term in bank:
        bank[term]["score"] = min(100, bank[term]["score"] + boost)
        bank[term]["last_hit"] = datetime.now(timezone.utc).isoformat()
        bank[term]["hit_count"] = bank[term].get("hit_count", 0) + 1


def decay_keywords(memory: dict, decay_amount: int = 5, threshold: int = 10):
    bank = memory.setdefault("keyword_bank", {})
    to_drop = [t for t, d in bank.items() if d.get("score", 50) - decay_amount < threshold]
    for term in to_drop:
        del bank[term]
    for term in bank:
        bank[term]["score"] = max(0, bank[term].get("score", 50) - decay_amount)


def get_active_keywords(memory: dict, min_score: int = 10) -> list:
    bank = memory.get("keyword_bank", {})
    return sorted(
        [{"term": k, **v} for k, v in bank.items() if v.get("score", 0) >= min_score],
        key=lambda x: x["score"],
        reverse=True
    )
