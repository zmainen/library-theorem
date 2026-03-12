"""Fig 2: Separation ratio + read distributions — demonstrates Thm 3."""
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
}


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
        agg[(cond, n)] = {
            "reads": reads,
            "mean_reads": np.mean(reads),
        }
    return agg


def plot(save=True):
    results = load()
    agg = aggregate(results)
    n_values = sorted(set(r["n"] for r in results if r["n"] <= 500))  # original N range

    fig, (ax_ratio, ax_violin) = plt.subplots(1, 2, figsize=(12, 5))

    # Left: separation ratio FLAT / INDEXED
    ratios, ratio_ns = [], []
    for n in n_values:
        flat = agg.get(("FLAT", n))
        idx  = agg.get(("INDEXED", n))
        if flat and idx and idx["mean_reads"] > 0:
            ratios.append(flat["mean_reads"] / idx["mean_reads"])
            ratio_ns.append(n)

    ax_ratio.plot(ratio_ns, ratios, color="#2ca02c", marker="o",
                  markersize=8, linewidth=2, label="FLAT / INDEXED reads")
    ns_t = np.linspace(min(ratio_ns), max(ratio_ns), 200)
    ax_ratio.plot(ns_t, ns_t / 20, color="#2ca02c", ls=":", alpha=0.4,
                  linewidth=1.2, label="N/20 (theory)")
    for n, r in zip(ratio_ns, ratios):
        ax_ratio.annotate(f"{r:.1f}×", (n, r), textcoords="offset points",
                          xytext=(0, 8), ha="center", fontsize=9, color="#2ca02c")
    ax_ratio.set_xlabel("Store size N", fontsize=12)
    ax_ratio.set_ylabel("Separation ratio (×)", fontsize=12)
    ax_ratio.set_title("FLAT ÷ INDEXED page reads", fontsize=13)
    ax_ratio.set_xticks(n_values)
    ax_ratio.set_ylim(bottom=0)
    ax_ratio.legend(fontsize=9)
    ax_ratio.grid(alpha=0.2)

    # Right: violin distributions
    violin_conditions = ["FLAT", "INDEXED", "INDEXED-CORRUPTED"]
    width = 0.22
    positions_base = np.arange(len(n_values))

    for ci, cond in enumerate(violin_conditions):
        s = CONDITION_STYLE[cond]
        offset = (ci - 1) * width
        data_list = [agg[(cond, n)]["reads"] for n in n_values if (cond, n) in agg]
        pos = positions_base[:len(data_list)] + offset
        vp = ax_violin.violinplot(data_list, positions=pos, widths=width * 0.9,
                                   showmedians=True, showextrema=False)
        vp["cmedians"].set_color(s["color"])
        vp["cmedians"].set_linewidth(2)
        for body in vp["bodies"]:
            body.set_facecolor(s["color"])
            body.set_alpha(0.35)
            body.set_edgecolor(s["color"])
        ax_violin.plot([], [], color=s["color"], linewidth=6,
                       alpha=0.5, label=s["label"])

    ax_violin.set_xticks(positions_base)
    ax_violin.set_xticklabels([f"N={n}" for n in n_values])
    ax_violin.set_ylabel("Page reads per trial", fontsize=12)
    ax_violin.set_title("Distribution of page reads", fontsize=13)
    ax_violin.set_ylim(bottom=0)
    ax_violin.legend(fontsize=9, loc="upper left")
    ax_violin.grid(alpha=0.2, axis="y")

    fig.suptitle("Fig 2: Separation and distributions — gap widens with N (Thm 3)", fontsize=12)
    plt.tight_layout()
    if save:
        out = FIGURES_DIR / "fig2_separation.png"
        fig.savefig(out, dpi=150, bbox_inches="tight")
        print(f"Saved {out}")


if __name__ == "__main__":
    plot()
