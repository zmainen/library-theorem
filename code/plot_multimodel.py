"""Fig 6: Multi-model comparison — FLAT-SORTED + INDEXED across gpt-4o-mini and gpt-5.4."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent.parent / "data"
FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"

FILES = {
    "gpt-4o-mini": RESULTS_DIR / "exp2_gpt-4o-mini.jsonl",
    "gpt-5.4": RESULTS_DIR / "exp2_gpt-5.4.jsonl",
}

CONDITIONS = ["FLAT", "FLAT-SORTED", "INDEXED", "DEEP-INDEXED"]

STYLE = {
    ("gpt-4o-mini", "FLAT"):         {"color": "#d62728", "ls": "-",  "marker": "o"},
    ("gpt-4o-mini", "FLAT-SORTED"):  {"color": "#ff7f0e", "ls": "-",  "marker": "^"},
    ("gpt-4o-mini", "INDEXED"):      {"color": "#1f77b4", "ls": "-",  "marker": "D"},
    ("gpt-4o-mini", "DEEP-INDEXED"): {"color": "#2ca02c", "ls": "-",  "marker": "s"},
    ("gpt-5.4", "FLAT-SORTED"):      {"color": "#ff7f0e", "ls": "--", "marker": "^"},
    ("gpt-5.4", "INDEXED"):          {"color": "#1f77b4", "ls": "--", "marker": "D"},
    ("gpt-5.4", "DEEP-INDEXED"):     {"color": "#2ca02c", "ls": "--", "marker": "s"},
}


def load_all():
    data = {}
    for model, path in FILES.items():
        trials = []
        with open(path) as f:
            for line in f:
                if line.strip():
                    t = json.loads(line)
                    if t.get("page_reads") is not None:
                        trials.append(t)
        data[model] = trials
    return data


def aggregate(trials):
    buckets = defaultdict(list)
    for t in trials:
        buckets[(t["condition"], t["n"])].append(t)
    agg = {}
    for (cond, n), ts in buckets.items():
        reads = [t["page_reads"] for t in ts]
        correct = [t["correct"] for t in ts]
        agg[(cond, n)] = {
            "median": np.median(reads),
            "q25": np.percentile(reads, 25),
            "q75": np.percentile(reads, 75),
            "acc": sum(correct) / len(correct) if correct else 0,
            "n_trials": len(ts),
        }
    return agg


def plot():
    data = load_all()
    aggs = {m: aggregate(ts) for m, ts in data.items()}

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    ax_mini, ax_5, ax_acc = axes

    # Panel 1: gpt-4o-mini reads
    model = "gpt-4o-mini"
    agg = aggs[model]
    n_vals = sorted(set(n for (c, n) in agg if c in CONDITIONS))
    for cond in CONDITIONS:
        key = (model, cond)
        if key not in STYLE:
            continue
        s = STYLE[key]
        xs, ys, lo, hi = [], [], [], []
        for n in n_vals:
            d = agg.get((cond, n))
            if d:
                xs.append(n); ys.append(d["median"])
                lo.append(d["q25"]); hi.append(d["q75"])
        if xs:
            ax_mini.plot(xs, ys, label=cond, color=s["color"], ls=s["ls"],
                         marker=s["marker"], markersize=7, linewidth=1.8)
            ax_mini.fill_between(xs, lo, hi, alpha=0.1, color=s["color"])

    ns_t = np.linspace(min(n_vals), max(n_vals), 200)
    ax_mini.plot(ns_t, ns_t / 20, color="gray", ls=":", alpha=0.5, linewidth=1, label="M/2P theory")
    ax_mini.set_xlabel("Item count M")
    ax_mini.set_ylabel("Median page reads")
    ax_mini.set_title("GPT-4o-mini", fontsize=12)
    ax_mini.legend(fontsize=8)
    ax_mini.grid(alpha=0.2)
    ax_mini.set_ylim(bottom=0)

    # Panel 2: gpt-5.4 reads
    model = "gpt-5.4"
    agg = aggs[model]
    n_vals_5 = sorted(set(n for (c, n) in agg if c in CONDITIONS))
    for cond in ["FLAT-SORTED", "INDEXED", "DEEP-INDEXED"]:
        key = (model, cond)
        if key not in STYLE:
            continue
        s = STYLE[key]
        xs, ys, lo, hi = [], [], [], []
        for n in n_vals_5:
            d = agg.get((cond, n))
            if d:
                xs.append(n); ys.append(d["median"])
                lo.append(d["q25"]); hi.append(d["q75"])
        if xs:
            ax_5.plot(xs, ys, label=cond, color=s["color"], ls=s["ls"],
                      marker=s["marker"], markersize=7, linewidth=1.8)
            ax_5.fill_between(xs, lo, hi, alpha=0.1, color=s["color"])

    ns_t5 = np.linspace(min(n_vals_5), max(n_vals_5), 200)
    ax_5.plot(ns_t5, np.log2(ns_t5 / 10 + 1), color="gray", ls=":", alpha=0.5,
              linewidth=1, label="log₂(N) theory")
    ax_5.set_xlabel("Item count M")
    ax_5.set_title("GPT-5.4", fontsize=12)
    ax_5.legend(fontsize=8)
    ax_5.grid(alpha=0.2)
    ax_5.set_ylim(bottom=0)

    # Panel 3: accuracy comparison (both models, FLAT-SORTED only)
    for model in ["gpt-4o-mini", "gpt-5.4"]:
        agg = aggs[model]
        ls = "-" if model == "gpt-4o-mini" else "--"
        for cond in ["FLAT-SORTED", "INDEXED"]:
            xs, ys = [], []
            n_vals_m = sorted(set(n for (c, n) in agg if c == cond))
            for n in n_vals_m:
                d = agg.get((cond, n))
                if d:
                    xs.append(n); ys.append(d["acc"])
            if xs:
                c = "#ff7f0e" if cond == "FLAT-SORTED" else "#1f77b4"
                ax_acc.plot(xs, ys, label=f"{model} {cond}",
                            color=c, ls=ls, marker="o", markersize=6, linewidth=1.8)

    ax_acc.set_xlabel("Item count M")
    ax_acc.set_ylabel("Accuracy")
    ax_acc.set_title("Accuracy comparison", fontsize=12)
    ax_acc.set_ylim(-0.05, 1.05)
    ax_acc.legend(fontsize=7, loc="lower left")
    ax_acc.grid(alpha=0.2)

    fig.suptitle(
        "Fig 6: Multi-model comparison — can sorting substitute for indexing?\n"
        "Solid = gpt-4o-mini · Dashed = gpt-5.4 · Shaded = IQR",
        fontsize=11)
    plt.tight_layout()

    for dest in [FIGURES_DIR]:
        out = dest / "fig6_multimodel.png"
        fig.savefig(out, dpi=150, bbox_inches="tight")
        print(f"Saved {out}")


if __name__ == "__main__":
    plot()
