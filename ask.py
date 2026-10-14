#!/usr/bin/env python3
"""Ask every model one question via OpenRouter, clean context, no tools. Appends to data/runs.jsonl."""
import json, os, sys, time, datetime, concurrent.futures as cf, urllib.request

MODELS = {
    "us": ["anthropic/claude-opus-5.5", "openai/gpt-6.1-sol", "google/gemini-4-argon",
           "x-ai/grok-4.7", "meta/muse-wonder"],
    "cn": ["moonshotai/kimi-k3", "deepseek/deepseek-v4.1-flash", "qwen/qwen3.8-flash"],
    "open": ["google/gemma-4-31b-it"],
}
QUESTIONS = {
    "cutoff": "What is your knowledge cutoff date?",
    "cutoff_month": "What is your knowledge cutoff date? Answer with the month and year only (format: Month YYYY).",
    "cutoff_forced": "What is your knowledge cutoff? Give your single best estimate as a month and year, even if uncertain. Reply with only \"Month YYYY\", nothing else.",
    "sota_top3": "What are the top 3 state-of-the-art large language models you know of? Reply with exactly 3 lines, format: Lab | Model | Version. Nothing else.",
    "sota": "What are the top state-of-the-art large language models you know of?",
}
SAMPLES = 5
MAX_TOKENS = 8000
TIMEOUT_S = 180
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "runs.jsonl")

def ask(model, q):
    body = {"model": model, "messages": [{"role": "user", "content": QUESTIONS[q]}],
            "max_tokens": MAX_TOKENS, "plugins": []}  # no tools, no web plugin, no system prompt
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", json.dumps(body).encode(),
        {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}", "Content-Type": "application/json"})
    t = time.time()
    try:
        r = json.load(urllib.request.urlopen(req, timeout=TIMEOUT_S))
        msg = r["choices"][0]["message"]
        rec = {"answer": msg.get("content"), "citations": msg.get("annotations"), "tool_calls": msg.get("tool_calls"),
               "served_by": r.get("provider"), "usage": r.get("usage")}
    except Exception as e:
        rec = {"error": str(e) + (" " + e.read().decode()[:500] if hasattr(e, "read") else "")}
    return {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "model": model, "q": q,
            "lab_group": next(g for g, ms in MODELS.items() if model in ms), "secs": round(time.time() - t, 1), **rec}

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "cutoff"
    only = sys.argv[2] if len(sys.argv) > 2 else ""
    jobs = [(m, q) for ms in MODELS.values() for m in ms if only in m for _ in range(SAMPLES)]
    with cf.ThreadPoolExecutor(len(jobs)) as ex, open(OUT, "a") as f:
        for rec in ex.map(lambda j: ask(*j), jobs):
            f.write(json.dumps(rec) + "\n"); f.flush()
            print(rec["model"], "|", (rec.get("answer") or rec.get("error") or "")[:300].replace("\n", " "))
