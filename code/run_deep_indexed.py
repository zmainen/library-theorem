#!/usr/bin/env python3
"""Run DEEP-INDEXED trials — extends existing data with retry logic.

Wraps experiment.run_trial with exponential backoff for 429 rate limits.

Usage:
    export OPENAI_API_KEY=sk-...
    python code/run_deep_indexed.py
    python code/run_deep_indexed.py --provider openrouter
"""
import json, os, sys, time
from pathlib import Path
from dataclasses import asdict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from experiment import run_trial, RESULTS_DIR, TrialResult
from openai import OpenAI

RESULTS_FILE = RESULTS_DIR / "deep_indexed_v5.jsonl"
MAX_RETRIES = 5
BASE_DELAY = 2.0


def run_trial_with_retry(n, trial, model, client, max_turns):
    """Run a DEEP-INDEXED trial, retrying on 429 rate-limit errors."""
    for attempt in range(MAX_RETRIES):
        result = run_trial("DEEP-INDEXED", n, trial, model, client, max_turns=max_turns)
        if result.error and "429" in result.error and attempt < MAX_RETRIES - 1:
            delay = BASE_DELAY * (2 ** attempt)
            print(f"    429 on N={n} t={trial}, retry {attempt+1} in {delay:.0f}s", flush=True)
            time.sleep(delay)
        else:
            return result
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run DEEP-INDEXED trials with retry")
    parser.add_argument("--provider", default="openai", choices=["openai", "openrouter"])
    args = parser.parse_args()

    if args.provider == "openrouter":
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            print("Set OPENROUTER_API_KEY", file=sys.stderr)
            sys.exit(1)
        client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
        model = "openai/gpt-4o-mini"
    else:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("Set OPENAI_API_KEY", file=sys.stderr)
            sys.exit(1)
        client = OpenAI(api_key=api_key)
        model = "gpt-4o-mini"

    # Load already-successful trials
    done = set()
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE) as f:
            for line in f:
                d = json.loads(line)
                if d.get("total_tokens", 0) > 0:
                    done.add((d["n"], d["trial"]))

    batches = [
        (1000, range(20, 50), 300),
        (2000, range(20, 50), 300),
        (3000, range(0, 20), 400),
        (5000, range(0, 20), 500),
    ]

    remaining = [(n, t, mt) for n, trials, mt in batches for t in trials if (n, t) not in done]
    total = len(remaining)
    count = 0
    token_total = 0

    print(f"Running {total} trials ({len(done)} already done)", flush=True)

    for n, trial, max_turns in remaining:
        count += 1
        result = run_trial_with_retry(n, trial, model, client, max_turns)
        with open(RESULTS_FILE, "a") as f:
            f.write(json.dumps(asdict(result)) + "\n")
        token_total += result.total_tokens
        status = "ok" if result.correct else "WRONG"
        if result.error:
            status = f"ERR: {result.error[:40]}"
        print(
            f"[{count}/{total}] N={n:5d} t={trial:3d}: "
            f"reads={result.page_reads:3d} sec_idx={result.section_index_reads} "
            f"tok={result.total_tokens:,d} {status}",
            flush=True,
        )
        time.sleep(0.5)

    print(f"\nDone. {count} trials, {token_total:,d} tokens total.")
    print(f"Results: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
