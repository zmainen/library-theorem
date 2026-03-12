# The Library Theorem

**A Formal Theory of Agentic Reasoning Capacity**

Zachary F. Mainen — Champalimaud Foundation, Lisbon

Paper on arXiv (forthcoming) · [Project page](https://zmainen.github.io/library-theorem/)

---

An AI agent with organized external memory retrieves information in logarithmic time; without it, retrieval is linear. At a million items, that's the difference between 20 operations and 500,000.

This repository contains the experiment code, data, and project page for the Library Theorem paper.

## Key results

The primary experiments use GPT-4o-mini as the retrieval agent:

| Store organization | 100 items | 500 items | 2,000 items |
|:-------------------|----------:|----------:|------------:|
| Random pages       |  6 reads  | 22 reads  | 133 reads   |
| Sorted pages       |  5 reads  | 21 reads  |     —       |
| Card catalog (index) | 1 read  |  1 read   |   1 read    |
| Hierarchical index |  1 read   |  1 read   |   1 read    |

Multi-model replication with GPT-5.4 shows that stronger models achieve near-optimal binary search on sorted pages (5 reads at 500 items vs 21 for GPT-4o-mini) — but the explicit index still wins 5-to-1, and the gap grows exponentially with store size.

## Repository structure

```
index.html          Project page (GitHub Pages)
figures/             Web-optimized figures
code/
  experiment.py      Main retrieval experiment (OpenAI API)
  generate_corpus.py Encyclopedia corpus for content experiments
  run_deep_indexed.py  Deep-indexed (hierarchical) condition
  plot_search.py     Fig 1: page reads + accuracy vs store size
  plot_separation.py Fig 2: exponential separation ratio
  plot_cost.py       Fig 3: token cost scaling
  plot_deep.py       Fig 4: deep-indexed vs flat index
  plot_content.py    Fig 5: parametric memory competition
  plot_multimodel.py Fig 6: multi-model comparison
data/
  *.jsonl            Raw experiment results (~1,994 trials)
```

## Running the experiment

Requires Python 3.11+ and an OpenAI API key.

```bash
pip install openai matplotlib numpy
export OPENAI_API_KEY=sk-...

# Run retrieval experiment (50 trials per condition)
python code/experiment.py --n 50 100 200 500 --trials 50

# Generate figures
python code/plot_search.py
python code/plot_separation.py
python code/plot_cost.py
python code/plot_multimodel.py
```

## License

Code: MIT. Paper: see arXiv listing.
