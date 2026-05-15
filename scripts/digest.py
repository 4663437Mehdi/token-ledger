"""Synthesize a daily digest using an LLM via OpenRouter (free tier)."""
import json
import os
import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

FREE_MODELS = [
    "deepseek/deepseek-v4-flash:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-4-31b-it:free",
]

SYSTEM = """You are the editor of "The Token Ledger", a daily newsletter for AI developers
tracking LLM API pricing and model availability changes across providers.

Rules:
- Cold, factual, data-first tone. No hype, no emojis.
- Lead with the most cost-impacting change.
- For each item, give: model name, what changed, the numbers, and who should care.
- Convert per-token prices to per-million-tokens for readability ($X.XX / 1M).
- If nothing meaningful changed, say so in one line and list 3 cheapest models today.
- Output clean Markdown. No preamble, no "Here is...". Start with a # H1 title.
- Max ~400 words total.
"""


def synthesize(diff, snapshot, date_str):
    cheapest = sorted(
        [m for m in snapshot.values() if m["prompt_price"] > 0],
        key=lambda m: m["prompt_price"],
    )[:5]
    payload_data = {
        "date": date_str,
        "added_count": len(diff["added"]),
        "removed_count": len(diff["removed"]),
        "price_change_count": len(diff["price_changes"]),
        "added": diff["added"][:15],
        "removed": diff["removed"][:15],
        "price_changes": diff["price_changes"][:15],
        "cheapest_today": cheapest,
        "total_models": len(snapshot),
    }
    user_prompt = f"Today is {date_str}. Write the digest from this JSON:\n\n{json.dumps(payload_data, indent=2)}"

    models = [os.environ["OPENROUTER_MODEL"]] if os.environ.get("OPENROUTER_MODEL") else FREE_MODELS
    headers = {
        "Authorization": f"Bearer {os.environ['OPENROUTER_KEY']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/4663437Mehdi/token-ledger",
        "X-Title": "The Token Ledger",
    }
    last_err = None
    for model in models:
        print(f"[digest] trying model: {model}")
        r = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.3,
            },
            timeout=120,
        )
        if r.status_code < 300:
            return r.json()["choices"][0]["message"]["content"].strip()
        print(f"[digest] {model} failed {r.status_code}: {r.text[:200]}")
        last_err = r
    last_err.raise_for_status()
