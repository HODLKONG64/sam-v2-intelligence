from fastapi import FastAPI
import json

app = FastAPI()

@app.get("/")
def home():
    return {"status": "SAM API live", "routes": ["/leaderboard"]}

@app.get("/leaderboard")
def leaderboard():
    with open("memory/memory.json") as f:
        data = json.load(f)

    entities = list(data["entities"].values())
    ranked = sorted(entities, key=lambda x: x["score"], reverse=True)

    return ranked
