"""Fig 1: Page reads + accuracy vs N — demonstrates Thms 1, 2, 3."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path

RESULTS_FILE = Path(__file__).resolve().parent.parent / "data/exp2_gpt-4o-mini.jsonl"
FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"

CONDITION_STYLE = {
    "FLAT":               {"color": "#d62728", "ls": "-",  "marker": "o", "label": "FLAT"},
    "INDEXED":            {"color": "#1f77b4", "ls": "-",  "marker": "D", "label": "INDEXED"},
    "INDEXED-CORRUPTED":  {"color": "#e377c2", "ls": "--", "marker": "x", "label": "INDEXED-CORRUPTED"},
    "DEEP-INDEXED":       {"color": "#2ca02c", "ls": "-",  "marker": "s", "label": "DEEP-INDEXED"},
}


def wilson_ci(k, n, z=1.96):
    if n == 0: return 0, 0, 0
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2*n)) / denom
    spread = z * np.sqrt(p*(1-p)/n + z**2/(4*n**2)) / denom
    return p, max(0, center - spread), min(1, center + spread)


def load():
    results = []
    with open(RESULTS_FILE) as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    return results


def aggregate(results):
    buckets = defaultdict(list)
    for r in results:
        buckets[(r["condition"], r["n"])].append(r)
    agg = {}
    for (cond, n), trials in buckets.items():
        reads = [t["page_reads"] for t in trials]
        correct = [t["correct"] for t in trials]
        k = sum(correct)
        acc, acc_lo, acc_hi = wilson_ci(k, len(correct))
        agg[(cond, n)] = {
            "median_reads": np.median(reads),
            "iqr_lo_reads": np.percentile(reads, 25),
            "iqr_hi_reads": np.percentile(reads, 75),
            "acc": acc, "acc_lo": acc_lo, "acc_hi": acc_hi,
        }
    return agg


def plot(save=True):
    results = load()
    agg = aggregate(results)
    n_values = sorted(set(r["n"] for r in results))
    conditions = list(CONDITION_STYLE.keys())

    fig, (ax_reads, ax_acc) = plt.subplots(1, 2, figsize=(12, 5))

    for cond in conditions:
        s = CONDITION_STYLE[cond]
        xs, ys, lo, hi = [], [], [], []
        for n in n_values:
            d = agg.get((cond, n))
            if d:
                xs.append(n); ys.append(d["median_reads"])
                lo.append(d["iqr_lo_reads"]); hi.append(d["iqr_hi_reads"])
        if xs:
            ax_reads.plot(xs, ys, label=s["label"],
                          color=s["color"], ls=s["ls"], marker=s["marker"],
                          markersize=7, linewidth=1.8)
            ax_reads.fill_between(xs, lo, hi, alpha=0.12, color=s["color"])

    ns_t = np.linspace(min(n_values), max(n_values), 200)
    ax_reads.plot(ns_t, ns_t / 20, color="#d62728", ls=":", alpha=0.4,
                  linewidth=1.2, label="M/2P (theory)")
    ax_reads.axhline(2, color="#1f77b4", ls=":", alpha=0.4,
                     linewidth=1.2, label="2 (theory)")
    ax_reads.set_xlabel("Item count M", fontsize=12)
    ax_reads.set_ylabel("Median page reads", fontsize=12)
    ax_reads.set_title("Page reads vs item count", fontsize=13)
    ax_reads.set_xticks(n_values)
    ax_reads.legend(fontsize=9)
    ax_reads.grid(alpha=0.2)
    ax_reads.set_ylim(bottom=0)

    for cond in conditions:
        s = CONDITION_STYLE[cond]
        xs, ys, los, his = [], [], [], []
        for n in n_values:
            d = agg.get((cond, n))
            if d:
                xs.append(n); ys.append(d["acc"])
                los.append(d["acc_lo"]); his.append(d["acc_hi"])
        if xs:
            ax_acc.plot(xs, ys, label=s["label"], color=s["color"],
                        ls=s["ls"], marker=s["marker"], markersize=7, linewidth=1.8)
            ax_acc.fill_between(xs, los, his, alpha=0.12, color=s["color"])

    ax_acc.set_xlabel("Item count M", fontsize=12)
    ax_acc.set_ylabel("Accuracy", fontsize=12)
    ax_acc.set_title("Accuracy vs store size", fontsize=13)
    ax_acc.set_xticks(n_values)
    ax_acc.set_ylim(-0.05, 1.05)
    ax_acc.legend(fontsize=9, loc="lower left")
    ax_acc.grid(alpha=0.2)

    fig.suptitle(
        "Fig 1: Search property — median page reads and accuracy (gpt-4o-mini)\n"
        "FLAT: O(M) · INDEXED: O(1) until TOC overflows · shaded bands: IQR",
        fontsize=11,
    )
    plt.tight_layout()
    if save:
        out = FIGURES_DIR / "fig1_search-property.png"
        fig.savefig(out, dpi=150, bbox_inches="tight")
        print(f"Saved {out}")


if __name__ == "__main__":
    plot()
