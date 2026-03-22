"""
Extraction Engine Agent
=======================
Merged agent that replaces three separate agents:
  - Breakdown Teacher  (atomic JSON fact extraction)
  - Spotter            (new entity / new fact detection)
  - Search Discoverer  (keyword generation for DuckDuckGo phase)

All three roles are fulfilled here to reduce latency, token cost, and
coordination errors while remaining fully DB-12 compliant — DB-12 only
requires helpers to exist, not a minimum count.

Rules respected: DB-10 (fact-only, no invention), DB-12 (helpers used
every cycle), DB-16 (keyword bank expanded from discoveries).
"""

from __future__ import annotations

import re
import string
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STOP_WORDS: set[str] = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "it", "its", "this",
    "that", "these", "those", "i", "we", "you", "he", "she", "they",
    "their", "our", "your", "his", "her", "not", "no", "as", "if",
    "about", "into", "than", "then", "so", "also",
}


def _tokenise(text: str) -> list[str]:
    """Return lower-cased words stripped of punctuation."""
    translator = str.maketrans("", "", string.punctuation)
    return [w.lower().translate(translator) for w in text.split() if w]


def _candidate_keywords(text: str, min_len: int = 4) -> list[str]:
    """Extract meaningful single-token keyword candidates."""
    tokens = _tokenise(text)
    return [t for t in tokens if t not in _STOP_WORDS and len(t) >= min_len]


# Named entity patterns — two capture groups:
#   Group 1: Title-case runs, e.g. "Alfie Blaze", "East London" → [A-Z][a-z]+
#   Group 2: ALL-CAPS runs,   e.g. "NULL THE PROPHET"           → [A-Z]{2,}
_NAMED_ENTITY_RE = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b"
    r"|"
    r"\b([A-Z]{2,}(?:\s+[A-Z]{2,}){0,3})\b"
)


# ---------------------------------------------------------------------------
# Main agent class
# ---------------------------------------------------------------------------

class ExtractionEngine:
    """
    Single merged extraction agent.  Accepts raw source text plus the
    current memory state and returns a structured result dict.
    """

    # Minimum character length for a sentence to be considered a fact.
    MIN_FACT_LEN: int = 20

    def extract(
        self,
        raw_text: str,
        memory: dict[str, Any],
        source_url: str = "",
    ) -> dict[str, Any]:
        """
        Run all three extraction roles against *raw_text*.

        Parameters
        ----------
        raw_text   : Raw source text from a crawled page.
        memory     : Current in-memory state (used for new-entity detection).
        source_url : Origin URL for citation tagging.

        Returns
        -------
        {
          "named_entities": [...],   # all entity names found
          "new_entities":   [...],   # entities not yet in memory
          "updated_entities": [...], # entities already in memory w/ new facts
          "facts_by_entity": {       # Breakdown Teacher output
              "EntityName": [
                  {"text": "...", "source": "...", "type": "lore"},
                  ...
              ]
          },
          "keywords": [...],         # Search Discoverer output (new keywords)
          "extracted_at": "ISO8601",
        }
        """
        existing_names: set[str] = set(memory.get("entities", {}).keys())
        existing_keywords: set[str] = set(
            memory.get("keyword_bank", {}).keys()
        )

        # ------------------------------------------------------------------
        # 1. NAMED ENTITY EXTRACTION  (Breakdown Teacher / Spotter)
        # ------------------------------------------------------------------
        raw_matches = _NAMED_ENTITY_RE.findall(raw_text)
        # findall returns tuples (group1, group2); pick whichever group matched
        found_names: list[str] = list(
            dict.fromkeys(g1 or g2 for g1, g2 in raw_matches if g1 or g2)
        )

        new_entities: list[str] = [n for n in found_names if n not in existing_names]
        updated_entities: list[str] = [n for n in found_names if n in existing_names]

        # ------------------------------------------------------------------
        # 2. ATOMIC FACT EXTRACTION  (Breakdown Teacher)
        # ------------------------------------------------------------------
        sentences = re.split(r"(?<=[.!?])\s+", raw_text.strip())
        facts_by_entity: dict[str, list[dict[str, str]]] = {}

        for name in found_names:
            entity_facts: list[dict[str, str]] = []
            for sentence in sentences:
                if name in sentence and len(sentence) >= self.MIN_FACT_LEN:
                    entity_facts.append(
                        {
                            "text": sentence.strip(),
                            "source": source_url,
                            "type": self._classify_fact(sentence),
                        }
                    )
            if entity_facts:
                facts_by_entity[name] = entity_facts

        # ------------------------------------------------------------------
        # 3. KEYWORD GENERATION  (Search Discoverer)
        # ------------------------------------------------------------------
        candidates = _candidate_keywords(raw_text)
        # Include entity names as keywords (lower-cased, underscore-joined)
        entity_keywords = [n.lower().replace(" ", "_") for n in found_names]
        all_new_keywords = list(
            dict.fromkeys(
                [k for k in candidates + entity_keywords if k not in existing_keywords]
            )
        )

        return {
            "named_entities": found_names,
            "new_entities": new_entities,
            "updated_entities": updated_entities,
            "facts_by_entity": facts_by_entity,
            "keywords": all_new_keywords,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_fact(sentence: str) -> str:
        """Simple heuristic fact-type classification."""
        s = sentence.lower()
        if any(w in s for w in ("born", "created", "founded", "origin", "began")):
            return "origin"
        if any(w in s for w in ("role", "position", "known as", "called", "leader")):
            return "role"
        if any(w in s for w in ("lore", "legend", "story", "myth", "tale")):
            return "lore_details"
        return "fact"
