"""Fetch raw data from public LLM provider sources."""
import json
import time
from pathlib import Path
import requests

SNAPSHOT_DIR = Path(__file__).resolve().parent.parent / "data"
SNAPSHOT_DIR.mkdir(exist_ok=True)


def fetch_openrouter_models():
    r = requests.get("https://openrouter.ai/api/v1/models", timeout=30)
    r.raise_for_status()
    data = r.json().get("data", [])
    return {
        m["id"]: {
            "id": m["id"],
            "name": m.get("name"),
            "context": m.get("context_length"),
            "prompt_price": float(m.get("pricing", {}).get("prompt", 0) or 0),
            "completion_price": float(m.get("pricing", {}).get("completion", 0) or 0),
            "created": m.get("created"),
        }
        for m in data
    }


def load_previous():
    p = SNAPSHOT_DIR / "latest.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def save_snapshot(snapshot):
    (SNAPSHOT_DIR / "latest.json").write_text(
        json.dumps(snapshot, indent=2), encoding="utf-8"
    )
    ts = time.strftime("%Y-%m-%d")
    (SNAPSHOT_DIR / f"snapshot-{ts}.json").write_text(
        json.dumps(snapshot, indent=2), encoding="utf-8"
    )


def diff_snapshots(old, new):
    added = [new[k] for k in new if k not in old]
    removed = [old[k] for k in old if k not in new]
    price_changes = []
    for k in new:
        if k in old:
            o, n = old[k], new[k]
            if o["prompt_price"] != n["prompt_price"] or o["completion_price"] != n["completion_price"]:
                price_changes.append({
                    "id": k,
                    "name": n.get("name"),
                    "old_prompt": o["prompt_price"],
                    "new_prompt": n["prompt_price"],
                    "old_completion": o["completion_price"],
                    "new_completion": n["completion_price"],
                })
    return {"added": added, "removed": removed, "price_changes": price_changes}
