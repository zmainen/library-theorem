#!/usr/bin/env python3
"""Run DEEP-INDEXED trials for revision — extends existing data.

Batch 1: N=1000 trials 20–49, N=2000 trials 20–49 (30 new each)
Batch 2: N=3000 trials 0–19, N=5000 trials 0–19 (20 new each)

Wraps run_trial with retry logic for 429 rate limits.
"""
import json, os, sys, time
from pathlib import Path
from dataclasses import asdict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from experiment import (
    make_store, pick_target, build_deep_indexed_pages,
    TrialResult, RESULTS_DIR, P, _SYSTEM, TOOLS,
)
from openai import OpenAI

RESULTS_FILE = RESULTS_DIR / "deep_indexed_v5.jsonl"
MAX_RETRIES = 5
BASE_DELAY = 2.0


def run_trial_with_retry(n, trial, model, client, max_turns):
    """Run a DEEP-INDEXED trial with retry on 429s at the API call level."""
    condition = "DEEP-INDEXED"
    store = make_store(n, seed=trial)
    target_key, target_val = pick_target(store, seed=trial)
    pages, toc, section_tocs = build_deep_indexed_pages(store, seed=trial)
    num_pages = len(pages)

    result = TrialResult(
        condition=condition, model=model, n=n,
        num_pages=num_pages, trial=trial,
        target_key=target_key, target_val=target_val,
    )

    system = _SYSTEM[condition].format(num_pages=num_pages, P=P, target_key=target_key)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Find the value for key {target_key}."},
    ]
    tools = TOOLS[condition]
    start = time.time()

    for turn in range(max_turns):
        # API call with retry
        resp = None
        for attempt in range(MAX_RETRIES):
            try:
                resp = client.chat.completions.create(
                    model=model, messages=messages, tools=tools,
                    max_tokens=256, temperature=0,
                )
                break
            except Exception as e:
                if "429" in str(e) and attempt < MAX_RETRIES - 1:
                    delay = BASE_DELAY * (2 ** attempt)
                    print(f"    429 on turn {turn}, retry {attempt+1} in {delay:.0f}s", flush=True)
                    time.sleep(delay)
                else:
                    result.error = str(e)[:200]
                    result.wall_time_s = time.time() - start
                    return result

        if resp is None:
            break

        result.num_turns = turn + 1
        if resp.usage:
            result.total_tokens += resp.usage.total_tokens

        msg = resp.choices[0].message
        if not msg.tool_calls:
            break

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ],
        })

        done = False
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            if name == "read_page":
                pn = int(args.get("page_num", 1))
                result.page_reads += 1
                if pn in pages:
                    entries = ", ".join(f"{k}->{v}" for k, v in pages[pn])
                    tool_result = f"Page {pn}: {entries}"
                else:
                    tool_result = f"Page {pn} not found. Valid range: 1-{num_pages}."
            elif name == "get_index":
                result.index_reads += 1
                tool_result = toc if toc else "No index available."
            elif name == "get_section_index":
                result.section_index_reads += 1
                sec_num = int(args.get("section_num", -1))
                if section_tocs and sec_num in section_tocs:
                    tool_result = section_tocs[sec_num]
                else:
                    valid = sorted(section_tocs.keys()) if section_tocs else []
                    tool_result = f"Section {sec_num} not found. Valid sections: {valid}."
            elif name == "submit_answer":
                value = args.get("value", "").strip().upper()[:4]
                result.answer = value
                result.answered = True
                result.correct = (value == target_val)
                tool_result = "Answer recorded."
                done = True
            else:
                tool_result = f"Unknown tool: {name}"

            messages.append({"role": "tool", "tool_call_id": tc.id, "content": tool_result})

        if done:
            break

    result.wall_time_s = time.time() - start
    return result


def main():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Set OPENROUTER_API_KEY", file=sys.stderr)
        sys.exit(1)
    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )
    model = "openai/gpt-4o-mini"

    # Load already-successful trials
    done = set()
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE) as f:
            for line in f:
                d = json.loads(line)
                if d.get("total_tokens", 0) > 0:  # skip failed 429 entries
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
        # Small delay between trials to avoid hammering the API
        time.sleep(0.5)

    print(f"\nDone. {count} trials, {token_total:,d} tokens total.")
    print(f"Results: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
