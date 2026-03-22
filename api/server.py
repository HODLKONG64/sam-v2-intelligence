from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import json
import os
from typing import Any, List

app = FastAPI()

MEMORY_FILE = "memory/memory.json"


class EvaluateInput(BaseModel):
    text: str


class SandboxSubmission(BaseModel):
    entity: str
    facts: List[str]
    sources: List[str]
    submitted_by: str = "api_user"


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {"entities": {}}
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


HTML_PAGE = '''
<!doctype html>
<html>
<head>
  <meta charset="UTF-8">
  <title>SAM // Moonboys Intelligence Dashboard</title>
  <style>
    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: Arial, sans-serif;
      background:
        radial-gradient(circle at top left, rgba(0,255,204,0.10), transparent 30%),
        radial-gradient(circle at top right, rgba(255,0,153,0.10), transparent 30%),
        linear-gradient(180deg, #07070b 0%, #0b0b12 100%);
      color: #f5f5f5;
    }

    .wrap {
      max-width: 1500px;
      margin: 0 auto;
      padding: 28px;
    }

    .hero, .panel, .card {
      border: 1px solid #242438;
      background: rgba(16,16,25,0.90);
      border-radius: 18px;
      box-shadow: 0 0 30px rgba(0,0,0,0.2);
    }

    .hero {
      padding: 24px;
      margin-bottom: 22px;
    }

    .hero h1 {
      margin: 0 0 8px;
      font-size: 48px;
      color: #fff;
    }

    .hero .sub {
      color: #aab0bc;
      font-size: 18px;
      margin-bottom: 18px;
    }

    .pulse {
      color: #00ffd0;
      font-weight: bold;
      animation: pulse 1.1s infinite alternate;
    }

    @keyframes pulse {
      from { opacity: 0.45; }
      to { opacity: 1; }
    }

    .top-grid {
      display: grid;
      grid-template-columns: 1.1fr 2fr 1fr;
      gap: 20px;
      align-items: start;
      margin-bottom: 24px;
    }

    .panel {
      padding: 20px;
    }

    .panel h2 {
      margin: 0 0 14px;
      font-size: 22px;
      color: #fff;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }

    .stat {
      background: #12121c;
      border: 1px solid #26263a;
      border-radius: 14px;
      padding: 14px;
    }

    .stat .k {
      font-size: 13px;
      color: #97a0b2;
      margin-bottom: 8px;
    }

    .stat .v {
      font-size: 26px;
      font-weight: bold;
      color: #fff;
    }

    .tokens-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .token {
      background: #12121c;
      border: 1px solid #26263a;
      border-radius: 14px;
      padding: 14px;
    }

    .token-name {
      font-weight: bold;
      font-size: 18px;
      color: #ffd54a;
      margin-bottom: 6px;
    }

    .token-price {
      font-size: 24px;
      font-weight: bold;
      color: #00ffd0;
    }

    .token-meta {
      color: #a2a8b7;
      font-size: 13px;
      margin-top: 4px;
    }

    textarea {
      width: 100%;
      min-height: 130px;
      resize: vertical;
      border-radius: 14px;
      border: 1px solid #2a2a40;
      background: #0f1018;
      color: #f5f5f5;
      padding: 14px;
      font-size: 15px;
      outline: none;
    }

    .form-row {
      display: flex;
      gap: 12px;
      margin-top: 12px;
      flex-wrap: wrap;
    }

    button {
      border: none;
      border-radius: 12px;
      padding: 14px 18px;
      font-weight: bold;
      cursor: pointer;
      min-width: 160px;
      font-size: 15px;
    }

    .btn-main {
      background: linear-gradient(90deg, #00ffd0, #1ea7ff);
      color: #061018;
    }

    .btn-danger {
      background: linear-gradient(90deg, #ff3b7a, #ff7b00);
      color: #fff;
    }

    .eval-result {
      margin-top: 14px;
      color: #ffd54a;
      font-weight: bold;
      min-height: 24px;
    }

    .leaderboard-wrap {
      display: grid;
      grid-template-columns: 1fr;
      gap: 18px;
    }

    .card {
      padding: 18px;
    }

    .card-top {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      margin-bottom: 12px;
    }

    .rank {
      font-size: 28px;
      font-weight: bold;
      color: #ffd54a;
    }

    .name {
      font-size: 28px;
      font-weight: bold;
      color: #fff;
    }

    .score-badge {
      font-size: 18px;
      font-weight: bold;
      color: #00ffd0;
      background: rgba(0,255,208,0.09);
      border: 1px solid rgba(0,255,208,0.25);
      border-radius: 999px;
      padding: 10px 14px;
      white-space: nowrap;
    }

    .bar-row {
      margin: 12px 0;
    }

    .label {
      font-size: 14px;
      color: #d7d7df;
      margin-bottom: 6px;
    }

    .bar {
      width: 100%;
      height: 12px;
      background: #23283b;
      border-radius: 999px;
      overflow: hidden;
    }

    .fill {
      height: 100%;
      border-radius: 999px;
    }

    .live-tag {
      display: inline-block;
      margin-top: 8px;
      font-size: 12px;
      color: #0b0b12;
      background: #00ffd0;
      border-radius: 999px;
      padding: 5px 10px;
      font-weight: bold;
    }

    .card-actions {
      margin-top: 14px;
    }

    .mini-btn {
      border: 1px solid #3b3144;
      background: #171722;
      color: #ff8fb3;
      border-radius: 10px;
      padding: 8px 12px;
      font-size: 13px;
      font-weight: bold;
      cursor: pointer;
      min-width: 0;
    }

    .legend {
      display: flex;
      gap: 14px;
      flex-wrap: wrap;
      margin-top: 18px;
      color: #a9b0be;
      font-size: 13px;
    }

    .dot {
      display: inline-block;
      width: 10px;
      height: 10px;
      border-radius: 999px;
      margin-right: 6px;
    }

    @media (max-width: 1200px) {
      .top-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <h1>SAM // MOONBOYS INTELLIGENCE</h1>
      <div class="sub">Autonomous lore scoring, rank monitoring, input evaluation, and persistent memory</div>
      <div class="pulse">SAM analysing...</div>
    </div>

    <div class="top-grid">
      <div class="panel">
        <h2>System Stats</h2>
        <div class="stats-grid">
          <div class="stat"><div class="k">Tracked Entities</div><div class="v" id="stat-entities">0</div></div>
          <div class="stat"><div class="k">Top Score</div><div class="v" id="stat-top">0</div></div>
          <div class="stat"><div class="k">Average Score</div><div class="v" id="stat-avg">0</div></div>
          <div class="stat"><div class="k">Saved Entries</div><div class="v" id="stat-submissions">0</div></div>
        </div>
      </div>

      <div class="panel">
        <h2>Evaluate New Input</h2>
        <textarea id="eval-text" placeholder="Paste text here."></textarea>
        <div class="form-row">
          <button class="btn-main" onclick="submitEvaluation()">Evaluate & Save</button>
          <button class="btn-danger" onclick="resetLiveEntries()">Reset Live Entries</button>
        </div>
        <div class="eval-result" id="eval-result"></div>
      </div>

      <div class="panel">
        <h2>Token Panel</h2>
        <div class="tokens-list">
          <div class="token">
            <div class="token-name">$PUNK</div>
            <div class="token-price">0.023</div>
            <div class="token-meta">Placeholder live token box</div>
          </div>
          <div class="token">
            <div class="token-name">$LFGK</div>
            <div class="token-price">0.047</div>
            <div class="token-meta">Placeholder live token box</div>
          </div>
          <div class="token">
            <div class="token-name">$PMSL</div>
            <div class="token-price">0.011</div>
            <div class="token-meta">Placeholder live token box</div>
          </div>
        </div>
      </div>
    </div>

    <div class="panel">
      <h2>Leaderboard</h2>
      <div class="leaderboard-wrap" id="board">Loading...</div>
      <div class="legend">
        <div><span class="dot" style="background:#00ffd0;"></span>Overall</div>
        <div><span class="dot" style="background:#4caf50;"></span>Completeness</div>
        <div><span class="dot" style="background:#2196f3;"></span>Consistency</div>
        <div><span class="dot" style="background:#ff9800;"></span>External</div>
        <div><span class="dot" style="background:#ff1d73;"></span>Freshness</div>
        <div><span class="dot" style="background:#a93ad8;"></span>Depth</div>
      </div>
    </div>
  </div>

  <script>
    function bar(value, color) {
      return '<div class="bar"><div class="fill" style="width:' + value + '%; background:' + color + ';"></div></div>';
    }

    async function loadBoard() {
      const res = await fetch("/leaderboard");
      const data = await res.json();

      let html = "";
      let totalScore = 0;
      let topScore = 0;
      let savedCount = 0;

      for (const e of data) {
        totalScore += e.score;
        if (e.score > topScore) topScore = e.score;
        if (e.is_live_submission) savedCount += 1;

        html += '<div class="card">';
        html += '<div class="card-top">';
        html += '<div>';
        html += '<div class="rank">#' + e.rank + '</div>';
        html += '<div class="name">' + e.name + '</div>';
        if (e.is_live_submission) {
          html += '<div class="live-tag">SAVED ENTRY</div>';
        }
        html += '</div>';
        html += '<div class="score-badge">Overall ' + e.score.toFixed(2) + '</div>';
        html += '</div>';

        html += '<div class="bar-row"><div class="label">Overall Score: ' + e.score.toFixed(2) + '</div>' + bar(e.score, '#00ffd0') + '</div>';
        html += '<div class="bar-row"><div class="label">Completeness: ' + e.completeness + '</div>' + bar(e.completeness, '#4caf50') + '</div>';
        html += '<div class="bar-row"><div class="label">Consistency: ' + e.consistency + '</div>' + bar(e.consistency, '#2196f3') + '</div>';
        html += '<div class="bar-row"><div class="label">External: ' + e.external + '</div>' + bar(e.external, '#ff9800') + '</div>';
        html += '<div class="bar-row"><div class="label">Freshness: ' + e.freshness + '</div>' + bar(e.freshness, '#ff1d73') + '</div>';
        html += '<div class="bar-row"><div class="label">Depth: ' + e.depth + '</div>' + bar(e.depth, '#a93ad8') + '</div>';

        if (e.is_live_submission) {
          html += '<div class="card-actions"><button class="mini-btn" onclick="deleteEntry(' + JSON.stringify(e.name) + ')">Delete Entry</button></div>';
        }

        html += '</div>';
      }

      document.getElementById("board").innerHTML = html;
      document.getElementById("stat-entities").textContent = data.length;
      document.getElementById("stat-top").textContent = data.length ? topScore.toFixed(2) : "0";
      document.getElementById("stat-avg").textContent = data.length ? (totalScore / data.length).toFixed(2) : "0";
      document.getElementById("stat-submissions").textContent = savedCount;
    }

    async function submitEvaluation() {
      const text = document.getElementById("eval-text").value;
      const result = document.getElementById("eval-result");

      if (!text.trim()) {
        result.textContent = "Paste some text first.";
        return;
      }

      const res = await fetch("/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text })
      });

      const data = await res.json();
      result.textContent = "Saved: " + data.name + " // score " + data.score.toFixed(2);
      document.getElementById("eval-text").value = "";
      loadBoard();
    }

    async function deleteEntry(name) {
      const result = document.getElementById("eval-result");

      const res = await fetch("/delete-entry/" + encodeURIComponent(name), {
        method: "DELETE"
      });

      const data = await res.json();
      result.textContent = data.message;
      loadBoard();
    }

    async function resetLiveEntries() {
      const result = document.getElementById("eval-result");

      const res = await fetch("/reset-live-entries", {
        method: "POST"
      });

      const data = await res.json();
      result.textContent = data.message;
      loadBoard();
    }

    loadBoard();
    setInterval(loadBoard, 2000);
  </script>
</body>
</html>
'''


@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_PAGE


@app.get("/status")
def status():
    return {
        "status": "SAM API live",
        "routes": [
            "/", "/leaderboard", "/status",
            "/evaluate", "/delete-entry/{name}", "/reset-live-entries",
            "/focus-plan", "/keyword-bank",
            "/bibles/{name}", "/sandbox/submit",
        ],
    }


@app.get("/leaderboard")
def leaderboard():
    data = load_memory()
    entities = list(data.get("entities", {}).values())
    ranked = sorted(entities, key=lambda x: x["score"], reverse=True)

    for i, e in enumerate(ranked):
        e["rank"] = i + 1

    return ranked


@app.post("/evaluate")
def evaluate(input_data: EvaluateInput):
    text = input_data.text.strip()
    words = text.split()

    data = load_memory()
    entities = data.get("entities", {})

    next_num = 1
    while f"LIVE ENTRY {next_num}" in entities:
        next_num += 1

    name = f"LIVE ENTRY {next_num}"
    score = float(len(text) % 100)

    entry = {
        "name": name,
        "completeness": min(100, max(10, len(words) * 4)),
        "consistency": min(100, 40 + (len(text) % 60)),
        "external": min(100, 20 + (len(words) % 50)),
        "freshness": 100,
        "depth": min(100, 15 + (len(text) % 70)),
        "score": score,
        "is_live_submission": True
    }

    entities[name] = entry
    data["entities"] = entities
    save_memory(data)

    return {
        "name": name,
        "input": text,
        "score": score,
        "saved": True
    }


@app.delete("/delete-entry/{name}")
def delete_entry(name: str):
    data = load_memory()
    entities = data.get("entities", {})

    if name not in entities:
        return {"deleted": False, "message": f"Entry not found: {name}"}

    if not entities[name].get("is_live_submission"):
        return {"deleted": False, "message": f"Refused. Not a live submission: {name}"}

    del entities[name]
    data["entities"] = entities
    save_memory(data)

    return {"deleted": True, "message": f"Deleted: {name}"}


@app.post("/reset-live-entries")
def reset_live_entries():
    data = load_memory()
    entities = data.get("entities", {})

    keep = {}
    removed = 0

    for name, entry in entities.items():
      if entry.get("is_live_submission"):
          removed += 1
      else:
          keep[name] = entry

    data["entities"] = keep
    save_memory(data)

    return {"reset": True, "removed": removed, "message": f"Removed {removed} live entries"}


# ---------------------------------------------------------------------------
# New endpoints — Focus Pipeline Layer
# ---------------------------------------------------------------------------

@app.get("/focus-plan")
def focus_plan():
    """
    Returns the Overmind focus plan so v1 knows which entities to target.
    Response shape:
      { "goal": str, "targets": [...], "stable": [...], "complete": [...] }
    """
    from intelligence.scoring_engine import score_entity
    from intelligence.ranking_engine import rank_entities
    from core.overmind import Overmind

    data = load_memory()
    entities = list(data.get("entities", {}).values())

    for e in entities:
        if "score" not in e:
            e["score"] = score_entity(e)

    ranked = rank_entities(entities)
    for i, e in enumerate(ranked):
        e["rank"] = i + 1

    overmind = Overmind()
    plan = overmind.analyse(data, ranked)
    return plan


@app.get("/keyword-bank")
def keyword_bank():
    """
    Return the full keyword bank with scores, sorted by score descending.
    """
    data = load_memory()
    bank = data.get("keyword_bank", {})
    sorted_bank = sorted(bank.values(), key=lambda x: x.get("score", 0), reverse=True)
    return {"keyword_bank": sorted_bank, "total": len(sorted_bank)}


@app.get("/bibles/{entity_name}")
def get_bible(entity_name: str):
    """
    Serve a specialist JSON bible for the given entity slug.
    Returns 404 if no bible exists yet (mention_count < 5).
    """
    import re

    def slugify(name: str) -> str:
        slug = re.sub(r"[^\w\s-]", "", name.lower()).strip()
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")
        if slug.startswith("sam-"):
            slug = slug[4:]
        return slug

    slug = slugify(entity_name)
    path = os.path.join("bibles", f"{slug}.json")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"No bible found for '{entity_name}'. Entity may not have reached 5 mentions yet.")

    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


@app.post("/sandbox/submit")
def sandbox_submit(submission: SandboxSubmission):
    """
    Accept an external contribution and write it to sandbox/incoming/.
    The ContributionGate will validate and promote it on the next cycle.

    Body:
      { "entity": str, "facts": [...], "sources": [...], "submitted_by": str }
    """
    import uuid
    from datetime import datetime, timezone

    os.makedirs(os.path.join("sandbox", "incoming"), exist_ok=True)

    payload = {
        "entity": submission.entity,
        "facts": submission.facts,
        "sources": submission.sources,
        "submitted_by": submission.submitted_by,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }

    filename = f"{uuid.uuid4().hex}.json"
    path = os.path.join("sandbox", "incoming", filename)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    return {
        "queued": True,
        "file": filename,
        "message": "Submission queued for validation. Will be processed on next cycle.",
    }
