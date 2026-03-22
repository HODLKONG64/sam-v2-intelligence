"""
Auto-Specialist Bible Generator
================================
Automatically creates a deep JSON "bible" file for any entity that has
reached mention_count >= 5.

Each bible contains:
  - all_facts (fully expanded)
  - relationships (other entities mentioned alongside)
  - timeline (facts ordered by discovery)
  - cross_links (related entity slugs for wiki navigation)

The wiki article for that entity becomes a light HTML shell that can
load the deep JSON dynamically, keeping HTML small at scale.

Rules respected: DB-11 (memory accumulates), DB-15 (master agent runs
this as part of its cycle), DB-47 (no 'sam-' prefix in filenames).
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any


BIBLE_DIR = "bibles"
MENTION_THRESHOLD = 5


def _slugify(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name.lower()).strip()
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if slug.startswith("sam-"):
        slug = slug[4:]
    return slug


def _build_bible(entity: dict[str, Any], all_entities: dict[str, Any]) -> dict[str, Any]:
    """Construct the full bible dict for a single entity."""
    name = entity.get("name", "Unknown")
    all_facts: list[str] = entity.get("all_facts", [])

    # Relationships: other entity names that appear inside this entity's facts
    other_names = [n for n in all_entities if n != name]
    relationships: list[str] = []
    for other in other_names:
        for fact in all_facts:
            if other in fact:
                if other not in relationships:
                    relationships.append(other)
                break

    # Timeline: facts labelled by their discovery position (index)
    timeline = [
        {"index": i + 1, "fact": f}
        for i, f in enumerate(all_facts)
    ]

    # Cross-links: URL slugs for related entities
    cross_links = [_slugify(r) for r in relationships]

    return {
        "name": name,
        "mention_count": entity.get("mention_count", 0),
        "score": entity.get("score", 0),
        "all_facts": all_facts,
        "relationships": relationships,
        "timeline": timeline,
        "cross_links": cross_links,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


class BibleGenerator:
    """
    Iterates over all entities in memory and creates/updates a JSON bible
    for every entity that has reached mention_count >= MENTION_THRESHOLD.
    """

    def __init__(self, bible_dir: str = BIBLE_DIR, threshold: int = MENTION_THRESHOLD):
        self.bible_dir = bible_dir
        self.threshold = threshold

    def run(self, memory: dict[str, Any]) -> dict[str, Any]:
        """
        Generate or refresh bibles for qualifying entities.

        Returns a summary:
        {
          "created": [...],   # entity names with freshly created bibles
          "updated": [...],   # entity names with refreshed bibles
          "skipped": [...],   # entity names below threshold
        }
        """
        os.makedirs(self.bible_dir, exist_ok=True)

        entities = memory.get("entities", {})
        created: list[str] = []
        updated: list[str] = []
        skipped: list[str] = []

        for name, entity in entities.items():
            if entity.get("mention_count", 0) < self.threshold:
                skipped.append(name)
                continue

            bible = _build_bible(entity, entities)
            slug = _slugify(name)
            path = os.path.join(self.bible_dir, f"{slug}.json")

            existed = os.path.exists(path)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(bible, fh, indent=2)

            if existed:
                updated.append(name)
            else:
                created.append(name)
                # Flag entity dirty so wiki publisher rebuilds its article
                # with a dynamic-load stub for the bible JSON.
                entity["dirty"] = True
                entity["bible_slug"] = slug

        return {"created": created, "updated": updated, "skipped": skipped}
