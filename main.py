from core.overmind import Overmind
from intelligence.scoring_engine import score_entity
from intelligence.ranking_engine import rank_entities
from memory.memory_manager import load_memory, save_memory

def run():

    memory = load_memory()
    overmind = Overmind()

    entities = memory.get("entities", {})

    # score all entities
    for name, e in entities.items():
        e["score"] = score_entity(e)

    # rank
    ranked = rank_entities(list(entities.values()))

    # assign ranks
    for i, e in enumerate(ranked):
        e["rank"] = i + 1

    memory["entities"] = {e["name"]: e for e in ranked}

    save_memory(memory)

    plan = overmind.analyse(memory, ranked)

    print("SAM GOAL:", plan["goal"])
    print("TARGETS:", plan["targets"])

if __name__ == "__main__":
    run()
