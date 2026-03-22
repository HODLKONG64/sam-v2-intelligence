def score_entity(entity: dict) -> float:
    """Score entity completeness 0-100. Higher = more complete/stable."""
    score = 0.0

    # Mention count (up to 30 points)
    mentions = entity.get("mention_count", 0)
    score += min(30, mentions * 3)

    # Fact count (up to 25 points)
    facts = entity.get("facts", [])
    score += min(25, len(facts) * 2)

    # Confirmed facts ratio (up to 20 points)
    if facts:
        confirmed = sum(1 for f in facts if isinstance(f, dict) and
                        f.get("status") in ("WEB_CONFIRMED", "CANON_CONFIRMED", "CROSS_CONFIRMED"))
        score += min(20, (confirmed / len(facts)) * 20)

    # Has relationships (up to 10 points)
    rels = entity.get("relationships", [])
    score += min(10, len(rels) * 2)

    # Has bible (10 points)
    if entity.get("has_bible", False):
        score += 10

    # Penalise dirty entities (needs update)
    if entity.get("dirty", False):
        score = max(0, score - 10)

    return round(score, 2)
