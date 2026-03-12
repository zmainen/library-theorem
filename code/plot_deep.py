"""Fig 4: INDEXED vs DEEP-INDEXED — two-level indexing restores O(1) retrieval."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path

RESULTS_FILES = [
    Path(__file__).resolve().parent.parent / "data/exp2_gpt-4o-mini.jsonl",
    Path(__file__).resolve().parent.parent / "data/deep_indexed_v5.jsonl",
]
OUT_DIR = Path(__file__).resolve().parent.parent / "figures"
OUT_DIR.mkdir(exist_ok=True)

STYLES = {
    "INDEXED":      {"color": "#1f77b4", "marker": "D", "ls": "-",  "label": "INDEXED (1-level)"},
    "DEEP-INDEXED": {"color": "#2ca02c", "marker": "s", "ls": "-",  "label": "DEEP-INDEXED (2-level)"},
    "FLAT":         {"color": "#d62728", "marker": "o", "ls": "--", "label": "FLAT (baseline)", "alpha": 0.4},
}


def wilson_ci(k, n, z=1.96):
    if n == 0: return 0, 0, 0
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2*n)) / denom
    spread = z * np.sqrt(p*(1-p)/n + z**2/(4*n**2)) / denom
    return p, max(0, center - spread), min(1, center + spread)


def load_and_aggregate():
    # Deduplicate: keep last entry per (condition, n, trial)
    seen = {}
    for rf in RESULTS_FILES:
        if not rf.exists():
            continue
        with open(rf) as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                if r.get("total_tokens", 0) == 0:
                    continue
                key = (r["condition"], r["n"], r["trial"])
                seen[key] = r

    buckets = defaultdict(list)
    for r in seen.values():
        buckets[(r["condition"], r["n"])].append(r)

    agg = {}
    for (cond, n), trials in buckets.items():
        reads = [t["page_reads"] for t in trials]
        tokens = [t["total_tokens"] for t in trials]
        k = sum(t["correct"] for t in trials)
        acc, acc_lo, acc_hi = wilson_ci(k, len(trials))
        agg[(cond, n)] = {
            "median_reads": np.median(reads),
            "iqr_lo_reads": np.percentile(reads, 25),
            "iqr_hi_reads": np.percentile(reads, 75),
            "mean_reads": np.mean(reads),
            "median_tokens": np.median(tokens),
            "iqr_lo_tokens": np.percentile(tokens, 25),
            "iqr_hi_tokens": np.percentile(tokens, 75),
            "acc": acc, "acc_lo": acc_lo, "acc_hi": acc_hi,
            "n_trials": len(trials),
        }
    return agg


def plot():
    agg = load_and_aggregate()

    # Focus on M values where both INDEXED and DEEP-INDEXED exist
    m_values = sorted(set(n for (c, n) in agg if c == "DEEP-INDEXED"))

    fig, (ax_reads, ax_tok, ax_acc) = plt.subplots(1, 3, figsize=(15, 4.5))

    # --- Panel 1: Page reads — median + IQR bands ---
    for cond in ["FLAT", "INDEXED", "DEEP-INDEXED"]:
        s = STYLES[cond]
        xs, ys, lo, hi = [], [], [], []
        for m in m_values:
            d = agg.get((cond, m))
            if d:
                xs.append(m); ys.append(d["median_reads"])
                lo.append(d["iqr_lo_reads"]); hi.append(d["iqr_hi_reads"])
        if xs:
            ax_reads.plot(xs, ys, label=s["label"],
                          color=s["color"], ls=s["ls"], marker=s["marker"],
                          markersize=7, linewidth=1.8,
                          alpha=s.get("alpha", 1.0))
            ax_reads.fill_between(xs, lo, hi, alpha=0.12, color=s["color"])

    # Crossover annotation
    idx_1k = agg.get(("INDEXED", 1000))
    if idx_1k:
        ax_reads.annotate("crossover", xy=(1000, idx_1k["median_reads"]),
                          xytext=(600, idx_1k["median_reads"] + 4),
                          fontsize=9, color="#555",
                          arrowprops=dict(arrowstyle="->", color="#555", lw=1.2))

    ax_reads.set_xlabel("Item count M", fontsize=11)
    ax_reads.set_ylabel("Median page reads (R)", fontsize=11)
    ax_reads.set_title("Page reads", fontsize=12)
    ax_reads.set_xscale("log")
    ax_reads.legend(fontsize=8, loc="upper left")
    ax_reads.grid(alpha=0.2)
    ax_reads.set_ylim(bottom=0)

    # --- Panel 2: Token cost (median + IQR) ---
    for cond in ["INDEXED", "DEEP-INDEXED"]:
        s = STYLES[cond]
        xs, ys, lo, hi = [], [], [], []
        for m in m_values:
            d = agg.get((cond, m))
            if d:
                xs.append(m); ys.append(d["median_tokens"])
                lo.append(d["iqr_lo_tokens"]); hi.append(d["iqr_hi_tokens"])
        if xs:
            ax_tok.plot(xs, ys, label=s["label"],
                        color=s["color"], ls=s["ls"], marker=s["marker"],
                        markersize=7, linewidth=1.8)
            ax_tok.fill_between(xs, lo, hi, alpha=0.12, color=s["color"])

    ax_tok.set_xlabel("Item count M", fontsize=11)
    ax_tok.set_ylabel("Median tokens (Tok)", fontsize=11)
    ax_tok.set_title("Token cost", fontsize=12)
    ax_tok.set_xscale("log")
    ax_tok.set_yscale("log")
    ax_tok.legend(fontsize=8)
    ax_tok.grid(alpha=0.2)

    # --- Panel 3: Accuracy ---
    for cond in ["INDEXED", "DEEP-INDEXED"]:
        s = STYLES[cond]
        xs, ys, los, his = [], [], [], []
        for m in m_values:
            d = agg.get((cond, m))
            if d:
                xs.append(m); ys.append(d["acc"])
                los.append(d["acc_lo"]); his.append(d["acc_hi"])
        if xs:
            ax_acc.plot(xs, ys, label=s["label"],
                        color=s["color"], ls=s["ls"], marker=s["marker"],
                        markersize=7, linewidth=1.8)
            ax_acc.fill_between(xs, los, his, alpha=0.12, color=s["color"])

    ax_acc.set_xlabel("Item count M", fontsize=11)
    ax_acc.set_ylabel("Accuracy", fontsize=11)
    ax_acc.set_title("Accuracy", fontsize=12)
    ax_acc.set_xscale("log")
    ax_acc.set_ylim(0.5, 1.05)
    ax_acc.legend(fontsize=8, loc="lower left")
    ax_acc.grid(alpha=0.2)

    fig.suptitle(
        "Two-level indexing: median page reads, tokens, and accuracy\n"
        "Shaded bands: interquartile range",
        fontsize=11,
    )
    plt.tight_layout()

    out = OUT_DIR / "fig4_deep-indexed.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"Saved {out}")



if __name__ == "__main__":
    plot()
