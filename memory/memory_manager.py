import json
import os
from datetime import datetime, timezone

import boto3
from botocore.config import Config


MEMORY_PATH = os.getenv("MEMORY_PATH", "memory/memory.json")

R2_BUCKET = os.environ.get("R2_BUCKET", "sam-memory")
R2_KEY = os.environ.get("R2_KEY", "sam-memory.json")
R2_ENDPOINT = (os.environ.get("R2_ENDPOINT_URL") or "").strip().rstrip("/") or None
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")


def _r2_enabled() -> bool:
    return all([R2_ENDPOINT, R2_ACCESS_KEY, R2_SECRET_KEY, R2_BUCKET, R2_KEY])


def _r2_client():
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


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
        "delivery": {
            "telegram": {
                "posted_ids": [],
                "last_post_at": None,
                "latest_lore": {},
            },
            "fandom": {
                "posted_ids": [],
                "last_post_at": None,
            },
        },
    }


def _merge_defaults(data: dict) -> dict:
    base = _empty_memory()
    for key, value in base.items():
        if key not in data:
            data[key] = value
        elif isinstance(value, dict):
            for sub_key, sub_val in value.items():
                if sub_key not in data[key]:
                    data[key][sub_key] = sub_val
                elif isinstance(sub_val, dict):
                    for sub_sub_key, sub_sub_val in sub_val.items():
                        if sub_sub_key not in data[key][sub_key]:
                            data[key][sub_key][sub_sub_key] = sub_sub_val
    return data


def load_memory() -> dict:
    if _r2_enabled():
        try:
            client = _r2_client()
            obj = client.get_object(Bucket=R2_BUCKET, Key=R2_KEY)
            data = json.loads(obj["Body"].read().decode("utf-8"))
            return _merge_defaults(data)
        except Exception as exc:
            print(f"[v2] R2 load failed: {exc}")

    if os.path.exists(MEMORY_PATH):
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return _merge_defaults(data)

    return _empty_memory()


def save_memory(memory: dict):
    memory = _merge_defaults(memory)
    payload = json.dumps(memory, indent=2, ensure_ascii=False).encode("utf-8")

    if _r2_enabled():
        try:
            client = _r2_client()
            client.put_object(
                Bucket=R2_BUCKET,
                Key=R2_KEY,
                Body=payload,
                ContentType="application/json",
            )
            print(f"[v2] memory saved to R2 ({R2_BUCKET}/{R2_KEY})")
        except Exception as exc:
            print(f"[v2] R2 save failed: {exc}")

    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
    with open(MEMORY_PATH, "wb") as f:
        f.write(payload)


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
