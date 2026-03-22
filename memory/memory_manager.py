import json
import os
from datetime import datetime

MEMORY_PATH = os.path.join(os.path.dirname(__file__), "memory.json")


def load_memory() -> dict:
    try:
        with open(MEMORY_PATH) as f:
            data = json.load(f)
        # Ensure all required keys exist
        data.setdefault("entities", {})
        data.setdefault("keyword_bank", {})
        data.setdefault("bibles", {})
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"entities": {}, "keyword_bank": {}, "bibles": {}}


def save_memory(memory: dict):
    with open(MEMORY_PATH, "w") as f:
        json.dump(memory, f, indent=2)


def add_keyword(memory: dict, term: str, initial_score: int = 50):
    bank = memory.setdefault("keyword_bank", {})
    if term not in bank:
        bank[term] = {
            "term": term,
            "score": initial_score,
            "last_hit": datetime.utcnow().isoformat(),
            "hit_count": 1
        }


def hit_keyword(memory: dict, term: str, boost: int = 5):
    bank = memory.setdefault("keyword_bank", {})
    if term in bank:
        bank[term]["score"] = min(100, bank[term].get("score", 50) + boost)
        bank[term]["last_hit"] = datetime.utcnow().isoformat()
        bank[term]["hit_count"] = bank[term].get("hit_count", 0) + 1


def decay_keywords(memory: dict, decay_amount: int = 5, threshold: int = 10):
    bank = memory.setdefault("keyword_bank", {})
    to_drop = [
        term for term, data in bank.items()
        if data.get("score", 50) - decay_amount < threshold
    ]
    for term in to_drop:
        del bank[term]
    for term in bank:
        bank[term]["score"] = max(0, bank[term].get("score", 50) - decay_amount)


def get_active_keywords(memory: dict, min_score: int = 10) -> list:
    bank = memory.get("keyword_bank", {})
    active = {k: v for k, v in bank.items() if v.get("score", 0) >= min_score}
    return sorted(active.values(), key=lambda x: x["score"], reverse=True)

