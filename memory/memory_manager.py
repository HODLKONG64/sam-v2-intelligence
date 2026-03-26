import json
import os
from datetime import datetime, timezone

MEMORY_PATH = os.getenv("MEMORY_PATH", "memory/memory.json")


def _empty_memory() -> dict:
    return {
        "last_update": "",
        "cycle_count": 0,
        "facts": {
            "characters": {},
            "real_people": {},
            "factions": {},
            "armies": {},
            "lore_locations": {},
            "mechanics": {},
            "tokens": {},
            "games": {},
            "events": {},
            "brands": {},
        },
        "external_facts": {
            "CONFIRMED": {},
            "UNVERIFIED": {},
            "rejected_count": 0,
        },
        "web_discovered": {
            "WEB_CONFIRMED": {},
            "WEB_UNVERIFIED": {},
        },
        "keyword_bank": {},
        "bibles": {},
        "latest_focus_plan": {},
    }


def load_memory() -> dict:
    if os.path.exists(MEMORY_PATH):
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        base = _empty_memory()
        for key, value in base.items():
            if key not in data:
                data[key] = value
            elif isinstance(value, dict):
                for sub_key, sub_val in value.items():
                    if sub_key not in data[key]:
                        data[key][sub_key] = sub_val
        return data

    return _empty_memory()


def save_memory(memory: dict):
    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)


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
