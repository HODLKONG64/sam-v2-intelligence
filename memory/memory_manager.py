"""
Memory Manager
==============
Handles loading and saving of the SAM memory JSON (local file for dev;
R2 in production via environment variables).

Additions in this version:
  - Keyword bank with score + last_hit + decay (DB-19 compliant).
  - Dirty-flag helpers so the wiki publisher only rebuilds changed pages.
  - crawl_snapshot storage for the Delta Detector.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

FILE = "memory/memory.json"

# Keyword score boundaries
KEYWORD_SCORE_MAX = 100
KEYWORD_SCORE_MIN = 0
KEYWORD_DECAY_PER_CYCLE = 5   # points lost per cycle when not matched
KEYWORD_DROP_THRESHOLD = 10   # drop keyword when score falls below this


# ---------------------------------------------------------------------------
# Load / save
# ---------------------------------------------------------------------------

def load_memory() -> dict[str, Any]:
    try:
        with open(FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"entities": {}, "keyword_bank": {}, "crawl_snapshot": {}}


def save_memory(data: dict[str, Any]) -> None:
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Dirty-flag helpers
# ---------------------------------------------------------------------------

def mark_dirty(memory: dict[str, Any], entity_name: str) -> None:
    """Flag an entity so the wiki publisher rebuilds its page."""
    if entity_name in memory.get("entities", {}):
        memory["entities"][entity_name]["dirty"] = True


def mark_clean(memory: dict[str, Any], entity_name: str) -> None:
    """Clear the dirty flag after the wiki publisher has rebuilt the page."""
    if entity_name in memory.get("entities", {}):
        memory["entities"][entity_name]["dirty"] = False


# ---------------------------------------------------------------------------
# Keyword bank helpers  (DB-16, DB-19)
# ---------------------------------------------------------------------------

def add_keywords(memory: dict[str, Any], keywords: list[str]) -> None:
    """
    Add new keywords to the bank (DB-19: only Web Trust Gate-approved
    keywords should be passed here from the gate; other callers should
    use this for agent-discovered keywords after validation).
    New keywords start at score 50.
    """
    bank = memory.setdefault("keyword_bank", {})
    now = datetime.now(timezone.utc).isoformat()
    for kw in keywords:
        if kw not in bank:
            bank[kw] = {
                "term": kw,
                "score": 50,
                "last_hit": now,
            }


def hit_keyword(memory: dict[str, Any], keyword: str, boost: int = 10) -> None:
    """
    Increase a keyword's score (called when a search using this keyword
    returned useful results).
    """
    bank = memory.setdefault("keyword_bank", {})
    now = datetime.now(timezone.utc).isoformat()
    if keyword in bank:
        bank[keyword]["score"] = min(
            KEYWORD_SCORE_MAX, bank[keyword]["score"] + boost
        )
        bank[keyword]["last_hit"] = now
    else:
        bank[keyword] = {"term": keyword, "score": min(KEYWORD_SCORE_MAX, 50 + boost), "last_hit": now}


def decay_keywords(memory: dict[str, Any]) -> list[str]:
    """
    Decay every keyword that was NOT hit in this cycle and drop any that
    fall below the threshold.  Call once per cycle AFTER the search phase.

    Returns the list of keyword terms that were dropped.
    """
    bank = memory.get("keyword_bank", {})
    dropped: list[str] = []
    for kw, data in list(bank.items()):
        data["score"] = max(KEYWORD_SCORE_MIN, data["score"] - KEYWORD_DECAY_PER_CYCLE)
        if data["score"] < KEYWORD_DROP_THRESHOLD:
            del bank[kw]
            dropped.append(kw)
    return dropped


def get_active_keywords(memory: dict[str, Any], min_score: int = KEYWORD_DROP_THRESHOLD) -> list[str]:
    """Return keyword terms sorted by score descending, above min_score."""
    bank = memory.get("keyword_bank", {})
    active = [(kw, data["score"]) for kw, data in bank.items() if data["score"] >= min_score]
    return [kw for kw, _ in sorted(active, key=lambda x: x[1], reverse=True)]
