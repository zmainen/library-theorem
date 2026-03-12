"""Fig 3: Token cost vs N — demonstrates Thm 4 (quadratic vs linear growth)."""
import json
import numpy as np
import matplotlib
import matplotlib.ticker
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
        tokens = [t["total_tokens"] for t in trials]
        agg[(cond, n)] = {
            "median_tokens": np.median(tokens),
            "iqr_lo": np.percentile(tokens, 25),
            "iqr_hi": np.percentile(tokens, 75),
        }
    return agg


def plot(save=True):
    results = load()
    agg = aggregate(results)
    n_values = sorted(set(r["n"] for r in results))
    conditions = ["FLAT", "INDEXED"]  # large-N run only has these two

    fig, (ax_tok, ax_ratio) = plt.subplots(1, 2, figsize=(12, 5))

    # Left: median tokens vs M
    for cond in conditions:
        s = CONDITION_STYLE[cond]
        xs, ys, lo, hi = [], [], [], []
        for n in n_values:
            d = agg.get((cond, n))
            if d:
                xs.append(n)
                ys.append(d["median_tokens"])
                lo.append(d["iqr_lo"]); hi.append(d["iqr_hi"])
        if xs:
            ax_tok.plot(xs, ys, label=s["label"],
                        color=s["color"], ls=s["ls"], marker=s["marker"],
                        markersize=7, linewidth=1.8)
            ax_tok.fill_between(xs, lo, hi, alpha=0.12, color=s["color"])

    ax_tok.set_xlabel("Item count M", fontsize=12)
    ax_tok.set_ylabel("Median tokens per trial", fontsize=12)
    ax_tok.set_title("Token cost vs item count (log scale)", fontsize=13)
    ax_tok.set_yscale("log")
    ax_tok.set_xscale("log")
    ax_tok.set_xticks(n_values)
    ax_tok.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax_tok.legend(fontsize=9)
    ax_tok.grid(alpha=0.2, which="both")

    # Right: token cost ratio FLAT / INDEXED
    ratios, ratio_ns = [], []
    for n in n_values:
        flat = agg.get(("FLAT", n))
        idx  = agg.get(("INDEXED", n))
        if flat and idx and idx["median_tokens"] > 0:
            ratios.append(flat["median_tokens"] / idx["median_tokens"])
            ratio_ns.append(n)

    ax_ratio.plot(ratio_ns, ratios, color="#8c564b", marker="o", markersize=8,
                  linewidth=2, label="FLAT / INDEXED tokens")
    for n, r in zip(ratio_ns, ratios):
        ax_ratio.annotate(f"{r:.1f}×", (n, r), textcoords="offset points",
                          xytext=(0, 8), ha="center", fontsize=9, color="#8c564b")

    # Log-log fit for slope
    log_ns = np.log(ratio_ns)
    log_rs = np.log(ratios)
    slope, intercept = np.polyfit(log_ns, log_rs, 1)
    ns_fit = np.linspace(min(ratio_ns), max(ratio_ns), 200)
    ax_ratio.plot(ns_fit, np.exp(intercept) * ns_fit**slope, color="#8c564b",
                  ls=":", alpha=0.5, linewidth=1.5, label=f"power fit N^{slope:.2f}")

    ax_ratio.set_xlabel("Item count M", fontsize=12)
    ax_ratio.set_ylabel("Token cost ratio (×)", fontsize=12)
    ax_ratio.set_title("FLAT ÷ INDEXED token cost", fontsize=13)
    ax_ratio.set_xticks(n_values)
    ax_ratio.set_ylim(bottom=0)
    ax_ratio.legend(fontsize=9)
    ax_ratio.grid(alpha=0.2)

    fig.suptitle(
        f"Fig 3: Token cost (median) — FLAT≈M², INDEXED≈M (ratio slope M^{slope:.2f}, theory M¹) (Thm 4)",
        fontsize=12)
    plt.tight_layout()
    if save:
        out = FIGURES_DIR / "fig3_cost.png"
        fig.savefig(out, dpi=150, bbox_inches="tight")
        print(f"Saved {out}")
    plt.show()


if __name__ == "__main__":
    plot()
