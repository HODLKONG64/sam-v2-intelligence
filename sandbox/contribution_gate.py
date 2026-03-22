"""
Multi-Bot Safe Contribution Layer — Pre-Memory Sandbox
======================================================
External bots / agents write contribution files to sandbox/incoming/.
NOTHING in that directory ever touches memory directly.

The ContributionGate reads pending files, runs them through a two-stage
validation pipeline (Validator → Trust Judge) and only promotes facts
that pass ALL checks into memory — preserving DB-10 (no hallucination),
DB-13 (3-rule validation: Canon Match + Cross-Confirmed + Site Credibility),
and DB-17 (web confirmation required for WEB_CONFIRMED status).

Incoming contribution file format (JSON):
{
  "entity": "EntityName",
  "facts": ["Fact 1.", "Fact 2."],
  "sources": ["https://source1.com", "https://source2.com"],
  "submitted_by": "bot_identifier",
  "submitted_at": "ISO8601"   // optional, set by gate if missing
}

Promotion rules (strict):
  - At least 2 unique source URLs must be supplied.
  - Facts must not conflict with existing canon (simple keyword check).
  - Site credibility list loaded from DB-14 pre-verified reputable sources.
  - Passing facts get status "WEB_CONFIRMED", failing get "WEB_UNVERIFIED".
  - WEB_CONFIRMED facts merge into memory["entities"][entity]["web_discovered"].
  - WEB_UNVERIFIED facts are stored separately and never mixed (DB-18).
  - Processed files are moved to sandbox/processed/ to prevent re-processing.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from typing import Any


INCOMING_DIR = os.path.join("sandbox", "incoming")
PROCESSED_DIR = os.path.join("sandbox", "processed")

# DB-14: pre-verified reputable sources (partial list for credibility check)
REPUTABLE_DOMAINS: set[str] = {
    "wikipedia.org",
    "everybodywiki.com",
    "decentraland.org",
    "ra.co",
    "nftplazas.com",
    "xrpl.to",
    "xrp.cafe",
    "neftyblocks.com",
    "nfthive.io",
    "atomichub.io",
    "graffpunks.live",
    "fandom.com",
    "substack.com",
    "medium.com",
}


def _domain(url: str) -> str:
    """Extract domain from URL for credibility check."""
    url = url.lower().removeprefix("https://").removeprefix("http://").removeprefix("www.")
    return url.split("/")[0]


def _is_credible(sources: list[str]) -> bool:
    """DB-14: at least one source must be from a reputable domain."""
    return any(_domain(s) in REPUTABLE_DOMAINS for s in sources)


def _has_enough_sources(sources: list[str]) -> bool:
    """DB-17: require 2+ unique source URLs."""
    return len(set(sources)) >= 2


def _facts_conflict(facts: list[str], entity: dict[str, Any]) -> bool:
    """
    Lightweight canon-conflict detector.
    Flags a contribution as conflicting if any submitted fact directly
    contradicts an existing verified fact (opposite polarity keywords).
    This is intentionally conservative — a real system would use an LLM.
    """
    existing_facts: list[str] = entity.get("all_facts", [])
    return any(
        _negates_existing_fact(new_fact, existing_facts)
        for new_fact in facts
    )


_NEGATION_MARKERS = ("not ", "never ", "no ", "false ", "incorrect ")


def _negates_existing_fact(new_fact: str, existing_facts: list[str]) -> bool:
    """
    Return True if *new_fact* appears to negate a keyword asserted in any
    existing fact (simple heuristic; real validation uses LLM + canon rules).
    """
    nf_lower = new_fact.lower()
    for ex_fact in existing_facts:
        ef_words = [w for w in ex_fact.lower().split() if len(w) > 4]
        for word in ef_words:
            for marker in _NEGATION_MARKERS:
                if marker + word in nf_lower:
                    return True
    return False


class ContributionGate:
    """
    Reads pending sandbox submissions, validates them, and promotes
    passing facts into the correct memory partition (WEB_CONFIRMED vs
    WEB_UNVERIFIED — never mixed, DB-18).
    """

    def __init__(
        self,
        incoming_dir: str = INCOMING_DIR,
        processed_dir: str = PROCESSED_DIR,
    ):
        self.incoming_dir = incoming_dir
        self.processed_dir = processed_dir

    def process(self, memory: dict[str, Any]) -> dict[str, Any]:
        """
        Scan incoming dir, validate each submission, update memory.

        Returns a summary:
        {
          "promoted": [...],    # (entity, fact) pairs that entered memory
          "quarantined": [...], # (entity, fact) pairs stored as UNVERIFIED
          "rejected": [...],    # filenames that failed hard checks
        }
        """
        os.makedirs(self.incoming_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)

        promoted: list[dict] = []
        quarantined: list[dict] = []
        rejected: list[str] = []

        pending = [
            f for f in os.listdir(self.incoming_dir)
            if f.endswith(".json") and not f.startswith(".")
        ]

        for filename in pending:
            path = os.path.join(self.incoming_dir, filename)
            try:
                with open(path, encoding="utf-8") as fh:
                    submission = json.load(fh)
            except (json.JSONDecodeError, OSError):
                rejected.append(filename)
                self._archive(path, filename)
                continue

            # Stamp submission time if missing
            if "submitted_at" not in submission:
                submission["submitted_at"] = datetime.now(timezone.utc).isoformat()

            entity_name: str = submission.get("entity", "").strip()
            facts: list[str] = submission.get("facts", [])
            sources: list[str] = submission.get("sources", [])

            # Hard reject: missing required fields
            if not entity_name or not facts or not sources:
                rejected.append(filename)
                self._archive(path, filename)
                continue

            # Determine status using DB-13 / DB-17 rules
            enough_sources = _has_enough_sources(sources)
            credible = _is_credible(sources)

            existing_entity = memory.get("entities", {}).get(entity_name, {})
            no_conflict = not _facts_conflict(facts, existing_entity)

            # WEB_CONFIRMED: 2+ unique URLs + 1 credible source + no conflict
            if enough_sources and credible and no_conflict:
                status = "WEB_CONFIRMED"
                self._promote_to_memory(memory, entity_name, facts, sources, status, submission)
                for f in facts:
                    promoted.append({"entity": entity_name, "fact": f, "status": status})
            else:
                status = "WEB_UNVERIFIED"
                self._store_unverified(memory, entity_name, facts, sources, submission)
                for f in facts:
                    quarantined.append({"entity": entity_name, "fact": f, "status": status, "reason": self._rejection_reason(enough_sources, credible, no_conflict)})

            self._archive(path, filename)

        return {"promoted": promoted, "quarantined": quarantined, "rejected": rejected}

    # ------------------------------------------------------------------
    # Memory update helpers
    # ------------------------------------------------------------------

    def _promote_to_memory(
        self,
        memory: dict[str, Any],
        entity_name: str,
        facts: list[str],
        sources: list[str],
        status: str,
        submission: dict,
    ) -> None:
        entities = memory.setdefault("entities", {})
        entity = entities.setdefault(entity_name, {"name": entity_name})

        # Merge into all_facts (dedup)
        existing = set(entity.get("all_facts", []))
        new_facts = [f for f in facts if f not in existing]
        entity.setdefault("all_facts", []).extend(new_facts)

        # Track in web_discovered (WEB_CONFIRMED partition, DB-18)
        web_disc = entity.setdefault("web_discovered", {"WEB_CONFIRMED": [], "WEB_UNVERIFIED": []})
        for f in new_facts:
            web_disc["WEB_CONFIRMED"].append({
                "fact": f,
                "sources": sources,
                "submitted_by": submission.get("submitted_by", "unknown"),
                "submitted_at": submission["submitted_at"],
            })

        entity["dirty"] = True
        entity["mention_count"] = entity.get("mention_count", 0) + len(new_facts)

    def _store_unverified(
        self,
        memory: dict[str, Any],
        entity_name: str,
        facts: list[str],
        sources: list[str],
        submission: dict,
    ) -> None:
        entities = memory.setdefault("entities", {})
        entity = entities.setdefault(entity_name, {"name": entity_name})
        web_disc = entity.setdefault("web_discovered", {"WEB_CONFIRMED": [], "WEB_UNVERIFIED": []})
        for f in facts:
            web_disc["WEB_UNVERIFIED"].append({
                "fact": f,
                "sources": sources,
                "submitted_by": submission.get("submitted_by", "unknown"),
                "submitted_at": submission["submitted_at"],
            })

    # ------------------------------------------------------------------
    # File management
    # ------------------------------------------------------------------

    def _archive(self, src_path: str, filename: str) -> None:
        """Move processed file to processed/ to prevent re-processing."""
        dest = os.path.join(self.processed_dir, filename)
        shutil.move(src_path, dest)

    @staticmethod
    def _rejection_reason(enough_sources: bool, credible: bool, no_conflict: bool) -> str:
        reasons = []
        if not enough_sources:
            reasons.append("insufficient sources (<2 unique URLs)")
        if not credible:
            reasons.append("no credible domain found (DB-14)")
        if not no_conflict:
            reasons.append("potential canon conflict detected (DB-13)")
        return "; ".join(reasons) if reasons else "unknown"
