import json

FILE = "memory/memory.json"

def load_memory():
    try:
        with open(FILE) as f:
            return json.load(f)
    except:
        return {"entities": {}}

def save_memory(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)
