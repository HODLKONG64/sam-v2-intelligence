import os
import datetime
from datetime import timezone

from memory.memory_manager import load_memory, save_memory, decay_keywords
from core.overmind import Overmind
from intelligence.scoring_engine import score_entity


def _iter_entities(memory: dict):
    facts = memory.get("facts", {})
    if not isinstance(facts, dict):
        return

    for category, entities in facts.items():
        if not isinstance(entities, dict):
            continue
        for name, data in entities.items():
            if not isinstance(data, dict):
                continue
            yield category, name, data


async def run_cycle():
    """Main v2 intelligence cycle: score → classify → decay → save."""
    print("[v2] Starting intelligence cycle...")
    memory = load_memory()

    for category, name, data in _iter_entities(memory):
        data["_score"] = score_entity(data, category=category, name=name)

    overmind = Overmind()
    plan = overmind.analyse(memory)

    memory["latest_focus_plan"] = plan
    memory["latest_focus_plan"]["generated_at"] = datetime.datetime.now(timezone.utc).isoformat()

    decay_keywords(memory)
    save_memory(memory)

    print(
        f"[v2] Cycle complete. "
        f"Targets: {len(plan.get('targets', []))}, "
        f"Stable: {len(plan.get('stable', []))}, "
        f"Complete: {len(plan.get('complete', []))}"
    )


if __name__ == "__main__":
    import uvicorn
    from api.server import app

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
