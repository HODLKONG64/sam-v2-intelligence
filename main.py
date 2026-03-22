# main.py — enhanced orchestration
# Order: sandbox gate → score/rank → Overmind → bible check → keyword decay → save

from memory.memory_manager import load_memory, save_memory, decay_keywords, get_active_keywords
from intelligence.scoring_engine import score_entity
from intelligence.ranking_engine import rank_entities
from core.overmind import Overmind


def run():
    memory = load_memory()
    entities = memory.get("entities", {})

    # Score all entities
    for name, data in entities.items():
        data["score"] = score_entity(data)

    # Rank
    ranked = rank_entities(list(entities.values()))
    for i, e in enumerate(ranked):
        e["rank"] = i + 1
    entities = {e["name"]: e for e in ranked}

    # Overmind classification
    overmind = Overmind()
    plan = overmind.analyse(entities)

    # Keyword decay
    decay_keywords(memory)

    # Save
    memory["entities"] = entities
    memory["last_focus_plan"] = plan
    save_memory(memory)

    print(f"[v2 Brain] Focus plan: {plan['stats']}")
    print(f"[v2 Brain] Targets: {plan['targets'][:10]}...")
    print(f"[v2 Brain] Active keywords: {len(get_active_keywords(memory))}")

    return plan


if __name__ == "__main__":
    run()

