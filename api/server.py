from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json

app = FastAPI()


# -------------------------------
# FRONTEND (LIVE DASHBOARD)
# -------------------------------
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SAM Live Leaderboard</title>
    <style>
        body {
            background: #0b0b0f;
            color: #f5f5f5;
            font-family: Arial, sans-serif;
            padding: 30px;
        }

        h1 {
            margin-bottom: 5px;
        }

        .sub {
            color: #aaa;
            margin-bottom: 20px;
        }

        .card {
            background: #15151d;
            border: 1px solid #2a2a35;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 20px;
        }

        .rank {
            color: #ffd54a;
            font-weight: bold;
        }

        .bar {
            height: 10px;
            border-radius: 5px;
            background: #333;
            margin-top: 5px;
            margin-bottom: 10px;
            overflow: hidden;
        }

        .fill {
            height: 100%;
            border-radius: 5px;
        }
    </style>
</head>
<body>

<h1>SAM LIVE LEADERBOARD</h1>
<div class="sub">Live entity scoring from your local SAM system</div>

<div id="board">Loading...</div>

<script>
async function loadBoard() {
    const res = await fetch('/leaderboard');
    const data = await res.json();

    document.getElementById('board').innerHTML = data.map(e => `
        <div class="card">
            <div class="rank">#${e.rank} - ${e.name}</div>
            <div><strong>Overall Score: ${e.score.toFixed(2)}</strong></div>

            <div>Completeness: ${e.completeness}</div>
            <div class="bar"><div class="fill" style="width:${e.completeness}%; background:#4caf50;"></div></div>

            <div>Consistency: ${e.consistency}</div>
            <div class="bar"><div class="fill" style="width:${e.consistency}%; background:#2196f3;"></div></div>

            <div>External: ${e.external}</div>
            <div class="bar"><div class="fill" style="width:${e.external}%; background:#ff9800;"></div></div>

            <div>Freshness: ${e.freshness}</div>
            <div class="bar"><div class="fill" style="width:${e.freshness}%; background:#e91e63;"></div></div>

            <div>Depth: ${e.depth}</div>
            <div class="bar"><div class="fill" style="width:${e.depth}%; background:#9c27b0;"></div></div>
        </div>
    `).join('');
}

// auto refresh every 2 seconds
setInterval(loadBoard, 2000);
loadBoard();
</script>

</body>
</html>
"""


# -------------------------------
# ROOT (LOAD UI)
# -------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_PAGE


# -------------------------------
# LEADERBOARD API
# -------------------------------
@app.get("/leaderboard")
def leaderboard():
    with open("memory/memory.json") as f:
        data = json.load(f)

    entities = list(data["entities"].values())

    ranked = sorted(entities, key=lambda x: x["score"], reverse=True)

    # add rank numbers
    for i, e in enumerate(ranked):
        e["rank"] = i + 1

    return ranked


# -------------------------------
# EVALUATION API (NEW)
# -------------------------------
@app.post("/evaluate")
def evaluate(input_data: dict):
    text = input_data.get("text", "")

    # basic scoring logic (placeholder)
    score = len(text) % 100

    return {
        "input": text,
        "score": score
    }
