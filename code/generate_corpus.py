#!/usr/bin/env python3
"""Generate synthetic encyclopedia corpus for Library Benchmark.

Uses a frequency-ranked English noun list. For each topic, prompts an LLM
to generate a single factual sentence. Saves as a static JSON corpus.

Usage:
    source ~/.secrets
    python3.11 generate_corpus.py --m 5000
    python3.11 generate_corpus.py --m 5000 --provider openrouter
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

from openai import OpenAI

CORPUS_DIR = Path(__file__).resolve().parent / "corpus"
CORPUS_DIR.mkdir(exist_ok=True)

# Common English nouns — frequency-ranked, filtered for single-word common nouns.
# We use a large static list and take alphabetically-sorted slices.
WORDLIST_FILE = CORPUS_DIR / "nouns_5000.txt"


def ensure_wordlist():
    """Generate a wordlist if it doesn't exist, using a curated set."""
    if WORDLIST_FILE.exists():
        return
    # Bootstrap: use a broad set of concrete, common English nouns.
    # This is a one-time generation — the list is committed to repo.
    print("Generating wordlist via LLM...", flush=True)

    client, model = get_client("openrouter")
    all_words = set()
    batch = 0
    while len(all_words) < 5500:
        batch += 1
        resp = client.chat.completions.create(
            model=model,
            messages=[{
                "role": "user",
                "content": (
                    f"List 500 common English nouns, one per line. "
                    f"Single words only, no proper nouns, no abbreviations. "
                    f"Concrete nouns preferred (things you can see, touch, or measure). "
                    f"Batch {batch} — avoid repeating words from prior batches. "
                    f"Just the words, no numbers or bullets."
                ),
            }],
            max_tokens=4000,
            temperature=0.8,
        )
        words = [w.strip().lower() for w in resp.choices[0].message.content.strip().split("\n")]
        words = [w for w in words if w and " " not in w and len(w) > 2 and w.isalpha()]
        all_words.update(words)
        print(f"  Batch {batch}: {len(words)} words, {len(all_words)} total", flush=True)
        time.sleep(0.5)

    sorted_words = sorted(all_words)[:5000]
    WORDLIST_FILE.write_text("\n".join(sorted_words) + "\n")
    print(f"Saved {len(sorted_words)} nouns to {WORDLIST_FILE}")


def load_wordlist(m: int) -> list[str]:
    """Load first m topics from the alphabetically sorted wordlist."""
    ensure_wordlist()
    words = [w.strip() for w in WORDLIST_FILE.read_text().strip().split("\n") if w.strip()]
    if m > len(words):
        print(f"Warning: requested {m} topics but only {len(words)} available", file=sys.stderr)
        m = len(words)
    return words[:m]


def get_client(provider: str) -> tuple[OpenAI, str]:
    if provider == "openrouter":
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            print("Set OPENROUTER_API_KEY", file=sys.stderr)
            sys.exit(1)
        return OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1"), "openai/gpt-4o-mini"
    else:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("Set OPENAI_API_KEY", file=sys.stderr)
            sys.exit(1)
        return OpenAI(api_key=api_key), "gpt-4o-mini"


def generate_facts(topics: list[str], client: OpenAI, model: str, batch_size: int = 50) -> list[dict]:
    """Generate one fact per topic in batches."""
    corpus = []
    for i in range(0, len(topics), batch_size):
        batch = topics[i:i + batch_size]
        topic_list = "\n".join(f"- {t}" for t in batch)
        for attempt in range(5):
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{
                        "role": "system",
                        "content": (
                            "You are writing entries for a factual encyclopedia. "
                            "For each topic, write exactly one sentence (15–25 words). "
                            "Be specific, concrete, and factual. No hedging, no opinions. "
                            "Format: TOPIC: Sentence."
                        ),
                    }, {
                        "role": "user",
                        "content": f"Write one fact for each topic:\n{topic_list}",
                    }],
                    max_tokens=batch_size * 60,
                    temperature=0.3,
                )
                break
            except Exception as e:
                if "429" in str(e) and attempt < 4:
                    time.sleep(2 ** attempt)
                    continue
                raise

        # Parse response
        lines = resp.choices[0].message.content.strip().split("\n")
        batch_facts = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Handle "- TOPIC: fact" or "TOPIC: fact"
            line = line.lstrip("- ").lstrip("•").strip()
            if ": " in line:
                topic_part, fact = line.split(": ", 1)
                topic_key = topic_part.strip().lower()
                # Fuzzy match to our topic list
                if topic_key in batch:
                    batch_facts[topic_key] = fact.strip()
                else:
                    # Try matching by prefix
                    for t in batch:
                        if topic_key.startswith(t) or t.startswith(topic_key):
                            batch_facts[t] = fact.strip()
                            break

        for t in batch:
            fact = batch_facts.get(t, f"The {t} is a subject of ongoing scientific study")
            corpus.append({"topic": t, "fact": fact})

        done = min(i + batch_size, len(topics))
        print(f"  [{done}/{len(topics)}] Generated {len(batch_facts)}/{len(batch)} facts", flush=True)
        time.sleep(0.3)

    return corpus


def main():
    parser = argparse.ArgumentParser(description="Generate encyclopedia corpus")
    parser.add_argument("--m", type=int, default=5000, help="Number of topics")
    parser.add_argument("--provider", default="openrouter", choices=["openrouter", "openai"])
    parser.add_argument("--batch-size", type=int, default=50)
    args = parser.parse_args()

    topics = load_wordlist(args.m)
    print(f"Loaded {len(topics)} topics (first: {topics[0]}, last: {topics[-1]})")

    corpus_file = CORPUS_DIR / f"corpus_{args.m}.json"
    if corpus_file.exists():
        existing = json.loads(corpus_file.read_text())
        if len(existing) == len(topics):
            print(f"Corpus already exists at {corpus_file} ({len(existing)} entries)")
            return
        print(f"Corpus exists but has {len(existing)} entries, regenerating for {len(topics)}")

    client, model = get_client(args.provider)
    print(f"Generating facts with {model} via {args.provider}...")
    corpus = generate_facts(topics, client, model, batch_size=args.batch_size)

    corpus_file.write_text(json.dumps(corpus, indent=2))
    print(f"\nSaved {len(corpus)} entries to {corpus_file}")

    # Validate
    topics_got = [e["topic"] for e in corpus]
    assert topics_got == topics, "Topic order mismatch"
    empty = [e for e in corpus if len(e["fact"]) < 10]
    if empty:
        print(f"Warning: {len(empty)} entries have short facts (<10 chars)")


if __name__ == "__main__":
    main()
