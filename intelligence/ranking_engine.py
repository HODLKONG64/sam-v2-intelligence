def rank_entities(entities: list) -> list:
    """Sort entities by score descending. Input: list of {name, score, data} dicts."""
    return sorted(entities, key=lambda x: x.get("score", 0), reverse=True)
