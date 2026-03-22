"""
Overmind — Entity Priority Engine
===================================
Analyses the scored + ranked entity list and classifies every entity into
one of three focus tiers:

  TARGETS  : Low-score entities, newly discovered entities, and recently
             updated entities.  v1 agents run ONLY on these.
  STABLE   : Mid-range entities.  Processed only when capacity allows.
  COMPLETE : Top-score entities.  Skipped unless a new mention arrives.

Returning all three tiers via analyse() lets v1 load the plan from
/focus-plan and skip heavy processing for STABLE and COMPLETE entities,
dramatically reducing per-cycle work without breaking any DB rule.

Rules respected:
  DB-11 (memory accumulation) — nothing is deleted.
  DB-12 (agents still used every cycle — just on fewer entities).
  DB-15 (single master agent sets the plan).
"""

from __future__ import annotations

from typing import Any


class Overmind:

    # Fraction of entities classified as TARGETS (bottom N%).
    TARGET_FRACTION: float = 0.20
    # Minimum / maximum target counts regardless of corpus size.
    TARGET_MIN: int = 5
    TARGET_MAX: int = 20

    def __init__(
        self,
        target_fraction: float | None = None,
        target_min: int | None = None,
        target_max: int | None = None,
    ):
        """
        Parameters are optional overrides; class-level defaults are used
        when not supplied, making the Overmind configurable without
        requiring code changes.
        """
        if target_fraction is not None:
            self.TARGET_FRACTION = target_fraction
        if target_min is not None:
            self.TARGET_MIN = target_min
        if target_max is not None:
            self.TARGET_MAX = target_max

    def analyse(self, memory: dict[str, Any], ranked: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Classify every entity and return the full focus plan.

        Returns
        -------
        {
          "goal": str,
          "targets": [name, ...],    # Process these every cycle
          "stable": [name, ...],     # Process only when capacity allows
          "complete": [name, ...],   # Skip unless new mention
        }
        """
        total = len(ranked)
        if total == 0:
            return {"goal": "Awaiting entities", "targets": [], "stable": [], "complete": []}

        target_count = max(
            self.TARGET_MIN,
            min(self.TARGET_MAX, int(total * self.TARGET_FRACTION)),
        )

        # Bottom N% by score are primary targets (weakest knowledge)
        bottom = ranked[-target_count:]

        # Also pull in newly discovered entities and recently updated ones
        new_entities = [e for e in ranked if e.get("is_new", False)]
        recently_updated = [e for e in ranked if e.get("recently_updated", False)]

        target_names: list[str] = list(
            dict.fromkeys(
                [e["name"] for e in bottom]
                + [e["name"] for e in new_entities]
                + [e["name"] for e in recently_updated]
            )
        )

        # Top N% are considered COMPLETE (high-quality, skip unless new mention)
        top_count = max(self.TARGET_MIN, int(total * self.TARGET_FRACTION))
        top = ranked[:top_count]
        complete_names = [e["name"] for e in top if e["name"] not in target_names]

        # Everything else is STABLE
        stable_names = [
            e["name"] for e in ranked
            if e["name"] not in target_names and e["name"] not in complete_names
        ]

        return {
            "goal": "Improve weakest entities",
            "targets": target_names,
            "stable": stable_names,
            "complete": complete_names,
        }
