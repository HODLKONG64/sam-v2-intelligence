from intelligence.scoring_engine import score_entity


class Overmind:
    def __init__(self, target_fraction=0.20, target_min=5, target_max=20):
        self.target_fraction = target_fraction
        self.target_min = target_min
        self.target_max = target_max

    def analyse(self, memory: dict) -> dict:
        """Classify all entities into TARGETS / STABLE / COMPLETE tiers."""
        facts = memory.get("facts", {})
        if not isinstance(facts, dict) or not facts:
            return {
                "targets": [],
                "stable": [],
                "complete": [],
                "scores": {},
                "total_entities": 0,
                "target_count": 0,
            }

        scored = []

        for category, entities in facts.items():
            if not isinstance(entities, dict):
                continue

            for name, data in entities.items():
                if not isinstance(data, dict):
                    continue

                s = score_entity(data, category=category, name=name)
                scored.append({
                    "name": name,
                    "category": category,
                    "score": s,
                    "data": data,
                })

        if not scored:
            return {
                "targets": [],
                "stable": [],
                "complete": [],
                "scores": {},
                "total_entities": 0,
                "target_count": 0,
            }

        scored.sort(key=lambda x: x["score"])
        total = len(scored)

        target_count = max(
            self.target_min,
            min(self.target_max, int(total * self.target_fraction))
        )
        complete_count = max(0, int(total * 0.20))

        targets_raw = scored[:target_count]
        complete_raw = scored[-complete_count:] if complete_count > 0 else []
        stable_raw = scored[target_count:total - complete_count] if complete_count > 0 else scored[target_count:]

        recently_updated = [
            e for e in stable_raw + complete_raw
            if e["data"].get("dirty", False) or e["data"].get("mention_count", 0) <= 1
        ]

        all_targets = list({f'{e["category"]}:{e["name"]}' for e in targets_raw + recently_updated})

        stable = [
            f'{e["category"]}:{e["name"]}'
            for e in stable_raw
            if f'{e["category"]}:{e["name"]}' not in all_targets
        ]
        complete = [
            f'{e["category"]}:{e["name"]}'
            for e in complete_raw
            if f'{e["category"]}:{e["name"]}' not in all_targets
        ]

        return {
            "targets": all_targets,
            "stable": stable,
            "complete": complete,
            "scores": {f'{e["category"]}:{e["name"]}': e["score"] for e in scored},
            "total_entities": total,
            "target_count": len(all_targets),
        }
