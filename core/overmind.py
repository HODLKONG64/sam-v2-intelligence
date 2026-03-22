from intelligence.scoring_engine import score_entity
from intelligence.ranking_engine import rank_entities


class Overmind:
    def __init__(self, target_fraction=0.20, target_min=5, target_max=20):
        self.target_fraction = target_fraction
        self.target_min = target_min
        self.target_max = target_max

    def analyse(self, memory: dict) -> dict:
        """Classify all entities into TARGETS / STABLE / COMPLETE tiers."""
        facts = memory.get("facts", {})
        if not facts:
            return {"targets": [], "stable": [], "complete": []}

        # Score all entities
        scored = []
        for name, data in facts.items():
            s = score_entity(data)
            scored.append({"name": name, "score": s, "data": data})

        # Sort ascending by score (lowest = needs most work = TARGET)
        scored.sort(key=lambda x: x["score"])
        total = len(scored)

        # Calculate target count
        target_count = max(
            self.target_min,
            min(self.target_max, int(total * self.target_fraction))
        )
        complete_count = max(0, int(total * 0.20))

        targets_raw = scored[:target_count]
        complete_raw = scored[-complete_count:] if complete_count > 0 else []
        stable_raw = scored[target_count:total - complete_count] if complete_count > 0 else scored[target_count:]

        # Also pull in newly discovered or recently updated entities as targets
        recently_updated = [
            e for e in stable_raw + complete_raw
            if e["data"].get("dirty", False) or e["data"].get("mention_count", 0) <= 1
        ]

        all_targets = list({e["name"] for e in targets_raw + recently_updated})

        return {
            "targets": all_targets,
            "stable": [e["name"] for e in stable_raw if e["name"] not in all_targets],
            "complete": [e["name"] for e in complete_raw if e["name"] not in all_targets],
            "scores": {e["name"]: e["score"] for e in scored},
            "total_entities": total,
            "target_count": len(all_targets)
        }
