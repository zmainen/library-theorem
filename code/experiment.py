#!/usr/bin/env python3
"""Exp 2: Multi-step external retrieval — search property.

Tests Theorems 1–3: FLAT requires O(N) page reads, INDEXED requires O(log N).
Tests Theorem 5: DEEP-INDEXED restores O(1) page reads when flat TOC exceeds model capacity.

Conditions:
  FLAT             pages in random order; read_page(n) only
  INDEXED          pages sorted + TOC; read_page(n) + get_index()
  INDEXED-CORRUPTED  TOC with shuffled ranges (causal control)
  DEEP-INDEXED     two-level hierarchical index; master TOC → section TOCs → pages

Primary metric: page_reads per trial.
Theory predicts FLAT ~ N/(2P), INDEXED ~ 2, gap widens with N.
DEEP-INDEXED predicted ~ 1 page read at all N (3 tool calls: master → section → page).
"""

import json
import os
import random
import string
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path

from openai import OpenAI

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

P = 10  # entries per page
SECTION_SIZE = 10  # pages per section (DEEP-INDEXED)
MAX_TURNS = 120  # default; override with --max-turns
RESULTS_DIR = Path(__file__).resolve().parent.parent / "data"
RESULTS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------

def make_store(n: int, seed: int) -> list[tuple[int, str]]:
    """N (key, value) pairs. Keys: 3-digit ints. Values: 4-letter strings."""
    rng = random.Random(seed)
    keys = rng.sample(range(1000, 10000), n)
    values = ["".join(rng.choices(string.ascii_uppercase, k=4)) for _ in range(n)]
    return list(zip(keys, values))


def pick_target(store: list, seed: int) -> tuple[int, str]:
    rng = random.Random(seed + 10000)
    return store[rng.randrange(len(store))]


def build_pages(store: list, condition: str, seed: int) -> tuple[dict, str | None]:
    """Return (pages dict, toc string or None).

    pages: {page_num (1-indexed): [(key, value), ...]}
    toc: key-range index text, or None for FLAT
    """
    rng = random.Random(seed + 20000)
    items = list(store)

    if condition == "FLAT":
        rng.shuffle(items)
        pages = {i // P + 1: items[i:i + P] for i in range(0, len(items), P)}
        return pages, None

    if condition == "FLAT-SORTED":
        sorted_items = sorted(items, key=lambda x: x[0])
        pages = {i // P + 1: sorted_items[i:i + P] for i in range(0, len(sorted_items), P)}
        return pages, None  # sorted but no TOC

    # INDEXED and INDEXED-CORRUPTED both use sorted pages
    sorted_items = sorted(items, key=lambda x: x[0])
    pages = {i // P + 1: sorted_items[i:i + P] for i in range(0, len(sorted_items), P)}

    if condition == "INDEXED":
        lines = ["KEY-RANGE INDEX:"]
        for pn, entries in sorted(pages.items()):
            lo, hi = entries[0][0], entries[-1][0]
            lines.append(f"  Page {pn}: keys {lo}–{hi}")
        return pages, "\n".join(lines)

    if condition == "INDEXED-CORRUPTED":
        ranges = [(e[0][0], e[-1][0]) for _, e in sorted(pages.items())]
        shuffled = list(ranges)
        rng.shuffle(shuffled)
        if shuffled == ranges and len(ranges) > 1:
            shuffled[0], shuffled[1] = shuffled[1], shuffled[0]
        lines = ["KEY-RANGE INDEX (may contain errors):"]
        for pn, (lo, hi) in enumerate(shuffled, 1):
            lines.append(f"  Page {pn}: keys {lo}–{hi}")
        return pages, "\n".join(lines)

    raise ValueError(f"Unknown condition: {condition}")


def build_deep_indexed_pages(store: list, seed: int) -> tuple[dict, str, dict]:
    """Two-level hierarchical index for DEEP-INDEXED condition.

    Returns (pages, master_toc, section_tocs).
    - pages: {page_num: [(key, value), ...]} — same as INDEXED
    - master_toc: string listing sections with key ranges
    - section_tocs: {section_num: string listing pages with key ranges}
    """
    sorted_items = sorted(store, key=lambda x: x[0])
    pages = {i // P + 1: sorted_items[i:i + P] for i in range(0, len(sorted_items), P)}
    num_pages = len(pages)

    # Group pages into sections
    section_tocs = {}
    master_lines = ["MASTER INDEX (sections with key ranges):"]
    page_nums = sorted(pages.keys())

    for sec_idx, start in enumerate(range(0, num_pages, SECTION_SIZE)):
        sec_num = sec_idx + 1
        sec_pages = page_nums[start:start + SECTION_SIZE]
        sec_lo = pages[sec_pages[0]][0][0]
        sec_hi = pages[sec_pages[-1]][-1][0]
        master_lines.append(f"  Section {sec_num}: keys {sec_lo}–{sec_hi}")

        # Build section-level TOC
        sec_lines = [f"SECTION {sec_num} INDEX (pages with key ranges):"]
        for pn in sec_pages:
            lo, hi = pages[pn][0][0], pages[pn][-1][0]
            sec_lines.append(f"  Page {pn}: keys {lo}–{hi}")
        section_tocs[sec_num] = "\n".join(sec_lines)

    return pages, "\n".join(master_lines), section_tocs


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

TOOL_READ_PAGE = {
    "type": "function",
    "function": {
        "name": "read_page",
        "description": "Read a page of the key-value store. Returns all entries on that page.",
        "parameters": {
            "type": "object",
            "properties": {
                "page_num": {"type": "integer", "description": "Page number (1-indexed)"}
            },
            "required": ["page_num"],
        },
    },
}

TOOL_GET_INDEX = {
    "type": "function",
    "function": {
        "name": "get_index",
        "description": "Get the index showing which key ranges are on which pages.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}

TOOL_SUBMIT = {
    "type": "function",
    "function": {
        "name": "submit_answer",
        "description": "Submit your final answer once you have found the value.",
        "parameters": {
            "type": "object",
            "properties": {
                "value": {"type": "string", "description": "The 4-letter value for the target key"}
            },
            "required": ["value"],
        },
    },
}

TOOL_GET_SECTION_INDEX = {
    "type": "function",
    "function": {
        "name": "get_section_index",
        "description": "Get the page-level index for a specific section.",
        "parameters": {
            "type": "object",
            "properties": {
                "section_num": {"type": "integer", "description": "Section number"}
            },
            "required": ["section_num"],
        },
    },
}

TOOLS = {
    "FLAT": [TOOL_READ_PAGE, TOOL_SUBMIT],
    "FLAT-SORTED": [TOOL_READ_PAGE, TOOL_SUBMIT],
    "INDEXED": [TOOL_READ_PAGE, TOOL_GET_INDEX, TOOL_SUBMIT],
    "INDEXED-CORRUPTED": [TOOL_READ_PAGE, TOOL_GET_INDEX, TOOL_SUBMIT],
    "DEEP-INDEXED": [TOOL_READ_PAGE, TOOL_GET_INDEX, TOOL_GET_SECTION_INDEX, TOOL_SUBMIT],
}

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_SYSTEM = {
    "FLAT": (
        "You are searching a key-value store split across {num_pages} pages "
        "({P} entries per page, random order). "
        "Your task: find the value for key {target_key}. "
        "Use read_page to read pages one at a time until you find the key, "
        "then call submit_answer with the 4-letter value. "
        "Read as few pages as necessary."
    ),
    "FLAT-SORTED": (
        "You are searching a key-value store split across {num_pages} pages "
        "({P} entries per page, sorted by key in ascending order). "
        "Your task: find the value for key {target_key}. "
        "Pages are numbered 1 to {num_pages}. Keys are sorted: page 1 has the smallest keys, "
        "page {num_pages} has the largest. You can read any page by number. "
        "Use read_page to read pages. You may use any search strategy. "
        "Call submit_answer with the 4-letter value when found."
    ),
    "INDEXED": (
        "You are searching a key-value store split across {num_pages} pages "
        "({P} entries per page, sorted by key). "
        "Your task: find the value for key {target_key}. "
        "Call get_index to see which page covers your key range, "
        "then read that page and call submit_answer with the 4-letter value."
    ),
    "INDEXED-CORRUPTED": (
        "You are searching a key-value store split across {num_pages} pages "
        "({P} entries per page, sorted by key). "
        "Your task: find the value for key {target_key}. "
        "An index is available via get_index, but it may contain errors. "
        "Use read_page and submit_answer to find and report the value."
    ),
    "DEEP-INDEXED": (
        "You are searching a key-value store split across {num_pages} pages "
        "({P} entries per page, sorted by key, organized into sections). "
        "Your task: find the value for key {target_key}. "
        "Call get_index to see which section covers your key range. "
        "Then call get_section_index with that section number to see its pages. "
        "Then read the target page and call submit_answer."
    ),
}

# ---------------------------------------------------------------------------
# Trial result
# ---------------------------------------------------------------------------

@dataclass
class TrialResult:
    condition: str
    model: str
    n: int
    num_pages: int
    trial: int
    target_key: int
    target_val: str
    answer: str = ""
    correct: bool = False
    answered: bool = False
    page_reads: int = 0
    index_reads: int = 0
    section_index_reads: int = 0
    num_turns: int = 0
    total_tokens: int = 0
    wall_time_s: float = 0.0
    error: str = ""

# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

def run_trial(
    condition: str,
    n: int,
    trial: int,
    model: str,
    client: OpenAI,
    max_turns: int = MAX_TURNS,
) -> TrialResult:
    store = make_store(n, seed=trial)
    target_key, target_val = pick_target(store, seed=trial)

    section_tocs = None
    if condition == "DEEP-INDEXED":
        pages, toc, section_tocs = build_deep_indexed_pages(store, seed=trial)
    else:
        pages, toc = build_pages(store, condition, seed=trial)
    num_pages = len(pages)

    result = TrialResult(
        condition=condition, model=model, n=n,
        num_pages=num_pages, trial=trial,
        target_key=target_key, target_val=target_val,
    )

    system = _SYSTEM[condition].format(
        num_pages=num_pages, P=P, target_key=target_key
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Find the value for key {target_key}."},
    ]
    tools = TOOLS[condition]
    start = time.time()

    for turn in range(max_turns):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                max_tokens=256,
                temperature=0,
            )
        except Exception as e:
            result.error = str(e)
            break

        result.num_turns = turn + 1
        if resp.usage:
            result.total_tokens += resp.usage.total_tokens

        msg = resp.choices[0].message
        if not msg.tool_calls:
            break  # model gave up or produced text

        # Append assistant turn
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
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
                    entries = ", ".join(f"{k}→{v}" for k, v in pages[pn])
                    tool_result = f"Page {pn}: {entries}"
                else:
                    tool_result = f"Page {pn} not found. Valid range: 1–{num_pages}."

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

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": tool_result,
            })

        if done:
            break

    result.wall_time_s = time.time() - start
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Exp 2: Multi-step external retrieval")
    parser.add_argument("--model", default="gpt-4o-mini",
                        help="Model ID (e.g. gpt-4o-mini, gpt-5.4, openai/gpt-5.4)")
    parser.add_argument("--n", type=int, nargs="+", default=[50, 100, 200, 500],
                        help="Store sizes to sweep")
    parser.add_argument("--conditions", nargs="+",
                        default=["FLAT", "INDEXED", "INDEXED-CORRUPTED"],
                        choices=["FLAT", "FLAT-SORTED", "INDEXED", "INDEXED-CORRUPTED", "DEEP-INDEXED"])
    parser.add_argument("--trials", type=int, default=50,
                        help="Trials per cell")
    parser.add_argument("--max-turns", type=int, default=MAX_TURNS,
                        help="Max agentic turns per trial (default 120; set higher for large N)")
    parser.add_argument("--provider", default="openai", choices=["openai", "openrouter"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.provider == "openrouter":
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            print("Error: set OPENROUTER_API_KEY", file=sys.stderr)
            sys.exit(1)
        client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
        if not args.model.startswith("openai/"):
            args.model = f"openai/{args.model}"
    else:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("Error: set OPENAI_API_KEY", file=sys.stderr)
            sys.exit(1)
        client = OpenAI(api_key=api_key)

    model_short = args.model.split("/")[-1]
    results_file = RESULTS_DIR / f"exp2_{model_short}.jsonl"

    n_total = len(args.n) * len(args.conditions) * args.trials
    print(f"Model:       {args.model}")
    print(f"N values:    {args.n}")
    print(f"Conditions:  {args.conditions}")
    print(f"Trials/cell: {args.trials}  ({n_total} total)")
    print(f"Output:      {results_file}")
    print()
    if args.dry_run:
        return

    max_turns = args.max_turns

    done = 0
    summary = {}  # (condition, n) → {page_reads, correct, answered}

    for n in args.n:
        for condition in args.conditions:
            reads_list = []
            correct_count = 0
            answered_count = 0

            for trial in range(args.trials):
                done += 1
                result = run_trial(condition, n, trial, args.model, client, max_turns=max_turns)

                with open(results_file, "a") as f:
                    f.write(json.dumps(asdict(result)) + "\n")

                reads_list.append(result.page_reads)
                correct_count += result.correct
                answered_count += result.answered

                sec_str = f"  sec_idx={result.section_index_reads}" if result.section_index_reads else ""
                print(
                    f"[{done:4d}/{n_total}] {condition:20s} N={n:4d} t={trial:3d}: "
                    f"reads={result.page_reads:3d}  idx={result.index_reads}"
                    f"{sec_str}  "
                    f"{'✓' if result.correct else '✗'}  "
                    f"{'ans' if result.answered else 'no-ans'}"
                    + (f"  ERR={result.error[:60]}" if result.error else "")
                )

            mean_reads = sum(reads_list) / len(reads_list)
            acc = correct_count / args.trials
            expected_flat = n / (2 * P)
            summary[(condition, n)] = {
                "mean_reads": mean_reads,
                "acc": acc,
                "answered": answered_count / args.trials,
            }
            print(
                f"  → acc={acc:.0%}  mean_reads={mean_reads:.1f}  "
                f"(FLAT expected ~{expected_flat:.0f}, INDEXED expected ~2)\n"
            )

    # Final summary table
    print("=" * 70)
    print("SUMMARY — mean page reads (theory: FLAT~N/20, INDEXED~2)")
    print("=" * 70)
    header = f"{'Condition':22s}" + "".join(f"  N={n:>4}" for n in args.n)
    print(header)
    print("-" * len(header))
    for condition in args.conditions:
        row = f"{condition:22s}"
        for n in args.n:
            d = summary.get((condition, n))
            row += f"  {d['mean_reads']:6.1f}" if d else "      —"
        print(row)
    print()
    print("=" * 70)
    print("SUMMARY — accuracy")
    print("=" * 70)
    print(header)
    print("-" * len(header))
    for condition in args.conditions:
        row = f"{condition:22s}"
        for n in args.n:
            d = summary.get((condition, n))
            row += f"  {d['acc']:5.0%} " if d else "      —"
        print(row)
    print()
    print(f"Results saved to {results_file}")


if __name__ == "__main__":
    main()
