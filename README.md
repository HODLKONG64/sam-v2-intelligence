# sam-v2-intelligence

Internal intelligence layer for the Crypto Moonboys wiki system.

## Role

v2 is the **authoritative scorer**. It reads shared memory (R2), scores entities and keywords, and writes back rankings. It does NOT decay keywords in v1 (that is v2's job alone).

## Stack

- FastAPI
- Cloudflare R2 (shared memory store)
- Python 3.11+

## API

### `GET /leaderboard`

Returns ranked wiki entities.

**Response shape:**
```json
{
  "leaderboard": [...],
  "generated_at": "ISO 8601",
  "total": 10
}
```

## Slug Rules

- Lowercase, hyphen-separated
- No `sam-` prefix permitted
- All `wiki_url` values use `/wiki/<slug>.html` format

## Pipeline

brain → memory → publisher → wiki → telegram
