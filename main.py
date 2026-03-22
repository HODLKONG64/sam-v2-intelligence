"""
SAM v2 Intelligence — Main Orchestrator
========================================
Full pipeline for one intelligence cycle:

  1. Load memory (local JSON or R2).
  2. Run ContributionGate — promote valid sandbox submissions.
  3. Score + rank all entities via intelligence engines.
  4. Run Overmind → TARGETS / STABLE / COMPLETE focus plan.
  5. Run BibleGenerator → auto-create JSON bibles at mention_count >= 5.
  6. Decay keyword bank.
  7. Save updated memory.
  8. Print SAM GOAL + TARGETS for v1 to consume.

The Delta Detector and Extraction Engine are imported and ready for use
by the v1 acquisition pipeline; they are not called here directly because
v2 does not perform crawling — it processes v1's memory output.
"""

from core.overmind import Overmind
from intelligence.scoring_engine import score_entity
from intelligence.ranking_engine import rank_entities
from memory.memory_manager import (
    load_memory,
    save_memory,
    decay_keywords,
)
from pipeline.bible_generator import BibleGenerator
from sandbox.contribution_gate import ContributionGate


def run():
    memory = load_memory()

    # ------------------------------------------------------------------
    # 1. Process any pending sandbox contributions
    # ------------------------------------------------------------------
    gate = ContributionGate()
    gate_result = gate.process(memory)
    if gate_result["promoted"]:
        print(f"[Sandbox] Promoted {len(gate_result['promoted'])} facts from external submissions.")
    if gate_result["quarantined"]:
        print(f"[Sandbox] Quarantined {len(gate_result['quarantined'])} facts (WEB_UNVERIFIED).")
    if gate_result["rejected"]:
        print(f"[Sandbox] Rejected {len(gate_result['rejected'])} malformed submissions.")

    # ------------------------------------------------------------------
    # 2. Score all entities
    # ------------------------------------------------------------------
    entities = memory.get("entities", {})
    for name, e in entities.items():
        e["score"] = score_entity(e)

    # ------------------------------------------------------------------
    # 3. Rank
    # ------------------------------------------------------------------
    ranked = rank_entities(list(entities.values()))
    for i, e in enumerate(ranked):
        e["rank"] = i + 1

    memory["entities"] = {e["name"]: e for e in ranked}

    # ------------------------------------------------------------------
    # 4. Overmind — produce TARGETS / STABLE / COMPLETE focus plan
    # ------------------------------------------------------------------
    overmind = Overmind()
    plan = overmind.analyse(memory, ranked)

    # ------------------------------------------------------------------
    # 5. Auto-Specialist Bible Generator
    # ------------------------------------------------------------------
    bible_gen = BibleGenerator()
    bible_result = bible_gen.run(memory)
    if bible_result["created"]:
        print(f"[Bibles] Created bibles for: {', '.join(bible_result['created'])}")
    if bible_result["updated"]:
        print(f"[Bibles] Updated bibles for: {', '.join(bible_result['updated'])}")

    # ------------------------------------------------------------------
    # 6. Keyword bank decay
    # ------------------------------------------------------------------
    dropped = decay_keywords(memory)
    if dropped:
        print(f"[Keywords] Dropped low-score keywords: {', '.join(dropped)}")

    # ------------------------------------------------------------------
    # 7. Save memory
    # ------------------------------------------------------------------
    save_memory(memory)

    # ------------------------------------------------------------------
    # 8. Output plan for v1 / logging
    # ------------------------------------------------------------------
    print("SAM GOAL:", plan["goal"])
    print("TARGETS:", plan["targets"])
    print("STABLE:", plan["stable"])
    print("COMPLETE:", plan["complete"])

    return plan


if __name__ == "__main__":
    run()
