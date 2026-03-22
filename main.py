import asyncio
import datetime
import os
from datetime import timezone

from memory.memory_manager import load_memory, save_memory, decay_keywords
from core.overmind import Overmind
from intelligence.scoring_engine import score_entity


async def run_cycle():
    """Main v2 intelligence cycle: score → classify → decay → save."""
    print("[v2] Starting intelligence cycle...")
    memory = load_memory()

    # Score and rank all entities
    facts = memory.get("facts", {})
    for name, data in facts.items():
        data["_score"] = score_entity(data)

    # Run Overmind classification
    overmind = Overmind()
    plan = overmind.analyse(memory)

    # Store the latest plan in memory for the API to serve
    memory["latest_focus_plan"] = plan
    memory["latest_focus_plan"]["generated_at"] = datetime.datetime.now(timezone.utc).isoformat()

    # Keyword decay
    decay_keywords(memory)

    # Save
    save_memory(memory)

    print(f"[v2] Cycle complete. Targets: {len(plan['targets'])}, Stable: {len(plan['stable'])}, Complete: {len(plan['complete'])}")


if __name__ == "__main__":
    import uvicorn
    from api.server import app
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
