def score_entity(entity: dict, category: str = "", name: str = "") -> float:
    """Score entity completeness 0-100. Higher = more complete/stable."""
    score = 0.0

    mentions = int(entity.get("mention_count", 0) or 0)
    score += min(30, mentions * 3)

    facts = entity.get("all_facts") or entity.get("facts") or []
    if isinstance(facts, dict):
        facts = list(facts.values())
    if not isinstance(facts, list):
        facts = []
    score += min(25, len(facts) * 2)

    if facts:
        confirmed = 0
        for fact in facts:
            if isinstance(fact, dict):
                status = fact.get("status")
                if status in (
                    "VERIFIED",
                    "CONFIRMED_EXTERNAL",
                    "WEB_CONFIRMED",
                    "CANON_CONFIRMED",
                    "CROSS_CONFIRMED",
                ):
                    confirmed += 1
        score += min(20, (confirmed / len(facts)) * 20 if len(facts) else 0)

    rels = entity.get("relationships", []) or []
    if not isinstance(rels, list):
        rels = []
    score += min(10, len(rels) * 2)

    has_bible = entity.get("has_bible", False)
    if not has_bible:
        has_bible = mentions >= 5
    if has_bible:
        score += 10

    lore = str(entity.get("lore_details", "") or "").strip()
    if lore:
        score += min(10, max(2, len(lore) // 150))

    if entity.get("dirty", False):
        score = max(0, score - 10)

    return round(min(score, 100), 2)
