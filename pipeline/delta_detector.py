"""
Delta Detector
==============
Compares the raw text from the current crawl cycle against the stored
snapshot from the previous cycle and returns ONLY the changed / new
text blocks.

Feeding only deltas into the agent pipeline means:
  - Agents process new information only
  - Memory still accumulates (DB-11 safe — nothing is deleted)
  - Massive speed gain at scale

Rules respected: DB-11 (accumulate, never delete), DB-21 (scan all
locked sources every run — the crawl still happens; only the *agent
input* is reduced).
"""

from __future__ import annotations

import hashlib
import re
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _block_hash(text: str) -> str:
    """Stable SHA-256 hash of a normalised text block."""
    normalised = re.sub(r"\s+", " ", text.strip()).lower()
    return hashlib.sha256(normalised.encode()).hexdigest()


def _split_blocks(text: str, min_words: int = 10) -> list[str]:
    """
    Split raw page text into meaningful blocks (paragraphs or sentences).
    Blocks shorter than *min_words* are dropped to avoid noise.
    """
    raw_blocks = re.split(r"\n{2,}|\r\n{2,}", text.strip())
    result: list[str] = []
    for block in raw_blocks:
        block = block.strip()
        if len(block.split()) >= min_words:
            result.append(block)
    return result


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

class DeltaDetector:
    """
    Stateless utility — accepts current + previous crawl snapshots and
    returns only the text blocks that have changed or are brand new.
    """

    def detect(
        self,
        current_pages: dict[str, str],
        previous_pages: dict[str, str],
    ) -> dict[str, Any]:
        """
        Parameters
        ----------
        current_pages  : {url: raw_text} from THIS cycle's crawl.
        previous_pages : {url: raw_text} from the LAST cycle (stored in memory).

        Returns
        -------
        {
          "changed": {url: [block, ...]},   # new/changed blocks per URL
          "new_urls": [url, ...],           # URLs not seen before
          "removed_urls": [url, ...],       # URLs that disappeared
          "unchanged_urls": [url, ...],     # fully identical pages (skip)
          "summary": {
              "total_pages": int,
              "changed_pages": int,
              "new_blocks": int,
          }
        }
        """
        prev_hashes: dict[str, set[str]] = {
            url: {_block_hash(b) for b in _split_blocks(text)}
            for url, text in previous_pages.items()
        }

        changed: dict[str, list[str]] = {}
        new_urls: list[str] = []
        unchanged_urls: list[str] = []
        new_blocks_total: int = 0

        for url, text in current_pages.items():
            blocks = _split_blocks(text)
            if url not in previous_pages:
                new_urls.append(url)
                changed[url] = blocks
                new_blocks_total += len(blocks)
                continue

            old_hashes = prev_hashes[url]
            new_blocks = [b for b in blocks if _block_hash(b) not in old_hashes]

            if new_blocks:
                changed[url] = new_blocks
                new_blocks_total += len(new_blocks)
            else:
                unchanged_urls.append(url)

        removed_urls = [u for u in previous_pages if u not in current_pages]

        return {
            "changed": changed,
            "new_urls": new_urls,
            "removed_urls": removed_urls,
            "unchanged_urls": unchanged_urls,
            "summary": {
                "total_pages": len(current_pages),
                "changed_pages": len(changed),
                "new_blocks": new_blocks_total,
            },
        }

    # ------------------------------------------------------------------
    # Convenience: build the previous_pages snapshot from memory
    # ------------------------------------------------------------------

    @staticmethod
    def snapshot_from_memory(memory: dict[str, Any]) -> dict[str, str]:
        """Return the crawl snapshot stored in memory (empty dict if none)."""
        return memory.get("crawl_snapshot", {})

    @staticmethod
    def store_snapshot(memory: dict[str, Any], current_pages: dict[str, str]) -> None:
        """Overwrite the crawl snapshot in memory with the current crawl."""
        memory["crawl_snapshot"] = current_pages
