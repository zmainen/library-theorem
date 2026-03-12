# The Library Theorem

**A Formal Theory of Agentic Reasoning Capacity**

Zachary F. Mainen — Champalimaud Foundation, Lisbon

Paper on arXiv (forthcoming) · [Project page](https://zmainen.github.io/library-theorem/)

---

A library is not a pile of books. What makes it a library is that you can find what you need — the knowledge is *accessible*, not just present. The difference is organization: catalogs, classification systems, shelf orders. These are old technologies, and they solve a problem so fundamental we rarely think about it: how do you retrieve one specific thing from among many?

The Library Theorem proves that this principle applies to AI with full mathematical force, and that the effect is exponential. An AI agent with an indexed knowledge store retrieves information in logarithmic time; without one, retrieval is linear. At a million items, that's the difference between 20 operations and 500,000.

## What we found

We built digital key-value stores organized in four ways — random, sorted, indexed, and hierarchically indexed — and asked AI models to find specific entries. Each "visit" is one read operation that fills the model's context window.

**GPT-4o-mini** (primary model, 934 trials):

| Store organization   | 100 items | 500 items | 2,000 items |
|:---------------------|----------:|----------:|------------:|
| Random pages         |  6 reads  | 22 reads  |  133 reads  |
| Sorted pages         |  5 reads  | 21 reads  |      —      |
| Card catalog (index) |  1 read   |  1 read   |    1 read   |
| Hierarchical index   |  1 read   |  1 read   |    1 read   |

Sorting alone barely helps — the model can't sustain binary search. It loses track of its bounds, overshoots, backtracks, and at 500 items is almost as slow as random scanning.

**GPT-5.4** (replication, 360 trials):

| Store organization   | 100 items | 500 items |
|:---------------------|----------:|----------:|
| Sorted pages         |  2 reads  |  5 reads  |
| Card catalog (index) |  1 read   |  1 read   |

The stronger model *can* binary search — 5 reads at 500 items is near the theoretical optimum. It's building an index in its head, doing mentally what a card catalog does physically. But the catalog still wins 5-to-1, and the gap grows exponentially with scale.

**When the AI thinks it already knows.** With familiar content (encyclopedia entries instead of random keys), the model bypasses its tools entirely and generates answers from training memory. Accuracy collapses from 100% to 27%. The index is perfect; the model doesn't use it. We call this *parametric memory competition*.

## Why it matters

Current AI scaling focuses on three axes: model size, data, and compute. The Library Theorem identifies a fourth — the organization of external knowledge — with exponential returns. Better infrastructure may matter as much as bigger models.

This has a second consequence: when an AI follows an external index, every retrieval step is visible and auditable. When it generates from parametric memory, the process is opaque. The Library Theorem gives a *performance* reason for external structure that aligns with a *governance* reason. Efficiency and transparency usually trade off; here they point the same way.

## Code and data

```
code/
  experiment.py        Main retrieval experiment (OpenAI API)
  run_deep_indexed.py  Hierarchical index condition
  generate_corpus.py   Encyclopedia corpus for content experiments
  plot_*.py            Figure generation (6 figures)
data/
  *.jsonl              Raw results (~1,994 trials across both models)
figures/               Web-optimized versions of all paper figures
index.html             Project page (served via GitHub Pages)
```

### Reproduce

```bash
pip install openai matplotlib numpy
export OPENAI_API_KEY=sk-...

python code/experiment.py --n 50 100 200 500 --trials 50
python code/plot_search.py
```

## License

Code: MIT. Paper: see arXiv listing.
