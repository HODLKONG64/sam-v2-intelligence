class Overmind:
    """
    Classifies entities into TARGETS / STABLE / COMPLETE tiers.

    - TARGETS: bottom `target_fraction` by score + newly created + recently updated
    - COMPLETE: top `target_fraction` by score
    - STABLE: everything else (skip this cycle)

    This is the core of the Focus Pipeline — v1 fetches this plan and only
    runs CrewAI agents on TARGETS + NEW entities.
    """

    def __init__(self, target_fraction=0.20, target_min=5, target_max=50,
                 complete_fraction=0.20):
        self.target_fraction = target_fraction
        self.target_min = target_min
        self.target_max = target_max
        self.complete_fraction = complete_fraction

    def analyse(self, entities: dict) -> dict:
        """
        entities: dict of {entity_name: {score: float, mention_count: int,
                           last_updated: str, created_at: str, ...}}

        Returns: {
            "targets": [...],    # entity names to process NOW
            "stable": [...],     # entity names to skip
            "complete": [...],   # entity names with high coverage
            "stats": {
                "total": int,
                "target_count": int,
                "stable_count": int,
                "complete_count": int
            }
        }
        """
        if not entities:
            return {
                "targets": [], "stable": [], "complete": [],
                "stats": {"total": 0, "target_count": 0, "stable_count": 0, "complete_count": 0}
            }

        # Sort by score ascending (lowest score = most needs attention)
        sorted_entities = sorted(entities.items(), key=lambda x: x[1].get("score", 0))
        total = len(sorted_entities)

        n_targets = min(
            self.target_max,
            max(self.target_min, int(total * self.target_fraction))
        )
        n_complete = max(1, int(total * self.complete_fraction))

        complete_names = [e[0] for e in sorted_entities[-n_complete:]]

        # Targets = bottom n by score + any newly created (no score yet)
        bottom_n = [e[0] for e in sorted_entities[:n_targets] if e[0] not in complete_names]

        # Also include entities with score == 0 or None (newly added)
        new_entities = [
            e[0] for e in sorted_entities
            if e[1].get("score", 0) == 0 and e[0] not in bottom_n and e[0] not in complete_names
        ]

        targets = list(dict.fromkeys(bottom_n + new_entities))  # deduped, order preserved
        stable = [e[0] for e in sorted_entities if e[0] not in targets and e[0] not in complete_names]

        return {
            "targets": targets,
            "stable": stable,
            "complete": complete_names,
            "stats": {
                "total": total,
                "target_count": len(targets),
                "stable_count": len(stable),
                "complete_count": len(complete_names)
            }
        }
