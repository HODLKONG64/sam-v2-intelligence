def rank_entities(entities):
    return sorted(entities, key=lambda x: x["score"], reverse=True)
