import json

with open("config/weights.json") as f:
    WEIGHTS = json.load(f)

def score_entity(e):

    return (
        e.get("completeness", 0) * WEIGHTS["completeness"] +
        e.get("consistency", 0) * WEIGHTS["consistency"] +
        e.get("external", 0) * WEIGHTS["external"] +
        e.get("freshness", 0) * WEIGHTS["freshness"] +
        e.get("depth", 0) * WEIGHTS["depth"]
    )
