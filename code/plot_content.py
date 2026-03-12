"""Fig 5: Three-content comparison — parametric memory competition."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / "figures"
OUT_DIR.mkdir(exist_ok=True)

SOURCES = {
    "Hash": [BASE / "data/exp2_gpt-4o-mini.jsonl",
             BASE / "data/deep_indexed_v5.jsonl"],
    "Numeric": [BASE / "data/benchmark_v3_numeric.jsonl"],
    "Encyclopedia": [BASE / "data/benchmark_v2.jsonl"],
}

CONTENT_STYLE = {
    "Hash":         {"color": "#1f77b4", "marker": "D", "ls": "-"},
    "Numeric":      {"color": "#2ca02c", "marker": "s", "ls": "-"},
    "Encyclopedia": {"color": "#d62728", "marker": "o", "ls": "-"},
}


def wilson_ci(k, n, z=1.96):
    if n == 0: return 0, 0, 0
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2*n)) / denom
    spread = z * np.sqrt(p*(1-p)/n + z**2/(4*n**2)) / denom
    return p, max(0, center - spread), min(1, center + spread)


def load_all():
    """Returns {content_type: {(condition, m): [trials]}}."""
    out = {}
    for ctype, files in SOURCES.items():
        seen = {}
        for rf in files:
            if not rf.exists():
                continue
            with open(rf) as f:
                for line in f:
                    if not line.strip():
                        continue
                    r = json.loads(line)
                    if r.get("total_tokens", 0) == 0:
                        continue
                    # benchmark_v2 files use "m" for store size; exp2 files use "n"
                    m = r.get("m", r.get("n"))
                    key = (r["condition"], m, r["trial"])
                    seen[key] = r
        buckets = defaultdict(list)
        for r in seen.values():
            m = r.get("m", r.get("n"))
            buckets[(r["condition"], m)].append(r)
        out[ctype] = buckets
    return out


def aggregate(trials):
    reads = [t["page_reads"] for t in trials]
    tokens = [t["total_tokens"] for t in trials]
    k = sum(t["correct"] for t in trials)
    n = len(trials)
    acc, acc_lo, acc_hi = wilson_ci(k, n)
    budget_fails = sum(1 for t in trials if "budget" in t.get("error", "").lower())
    return {
        "med_reads": np.median(reads),
        "iqr_lo_reads": np.percentile(reads, 25),
        "iqr_hi_reads": np.percentile(reads, 75),
        "med_tokens": np.median(tokens),
        "iqr_lo_tokens": np.percentile(tokens, 25),
        "iqr_hi_tokens": np.percentile(tokens, 75),
        "acc": acc, "acc_lo": acc_lo, "acc_hi": acc_hi,
        "n": n, "budget_fails": budget_fails,
    }


def plot():
    data = load_all()

    # Focus on DEEP-INDEXED condition — the key comparison
    condition = "DEEP-INDEXED"
    m_common = [50, 100, 200, 500]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    ax_reads, ax_tok, ax_acc = axes

    for ctype in ["Hash", "Numeric", "Encyclopedia"]:
        s = CONTENT_STYLE[ctype]
        buckets = data[ctype]
        xs, med_r, lo_r, hi_r = [], [], [], []
        med_t, lo_t, hi_t = [], [], []
        accs, acc_los, acc_his = [], [], []

        for m in m_common:
            trials = buckets.get((condition, m))
            if not trials:
                continue
            a = aggregate(trials)
            xs.append(m)
            med_r.append(a["med_reads"])
            lo_r.append(a["iqr_lo_reads"])
            hi_r.append(a["iqr_hi_reads"])
            med_t.append(a["med_tokens"])
            lo_t.append(a["iqr_lo_tokens"])
            hi_t.append(a["iqr_hi_tokens"])
            accs.append(a["acc"])
            acc_los.append(a["acc_lo"])
            acc_his.append(a["acc_hi"])

        if not xs:
            continue

        # Page reads
        ax_reads.plot(xs, med_r, label=ctype,
                      color=s["color"], ls=s["ls"], marker=s["marker"],
                      markersize=8, linewidth=2)
        ax_reads.fill_between(xs, lo_r, hi_r, alpha=0.12, color=s["color"])

        # Token cost
        ax_tok.plot(xs, med_t, label=ctype,
                    color=s["color"], ls=s["ls"], marker=s["marker"],
                    markersize=8, linewidth=2)
        ax_tok.fill_between(xs, lo_t, hi_t, alpha=0.12, color=s["color"])

        # Accuracy
        ax_acc.plot(xs, accs, label=ctype,
                    color=s["color"], ls=s["ls"], marker=s["marker"],
                    markersize=8, linewidth=2)
        ax_acc.fill_between(xs, acc_los, acc_his, alpha=0.12, color=s["color"])

    # Panel 1: Page reads
    ax_reads.set_xlabel("Item count M", fontsize=11)
    ax_reads.set_ylabel("Median page reads", fontsize=11)
    ax_reads.set_title("Page reads (DEEP-INDEXED)", fontsize=12)
    ax_reads.set_xscale("log")
    ax_reads.legend(fontsize=9)
    ax_reads.grid(alpha=0.2)
    ax_reads.set_ylim(-0.2, 5)

    # Panel 2: Token cost
    ax_tok.set_xlabel("Item count M", fontsize=11)
    ax_tok.set_ylabel("Median tokens", fontsize=11)
    ax_tok.set_title("Token cost (DEEP-INDEXED)", fontsize=12)
    ax_tok.set_xscale("log")
    ax_tok.set_yscale("log")
    ax_tok.legend(fontsize=9)
    ax_tok.grid(alpha=0.2)

    # Panel 3: Accuracy
    ax_acc.set_xlabel("Item count M", fontsize=11)
    ax_acc.set_ylabel("Accuracy", fontsize=11)
    ax_acc.set_title("Accuracy (DEEP-INDEXED)", fontsize=12)
    ax_acc.set_xscale("log")
    ax_acc.set_ylim(0.0, 1.05)
    ax_acc.legend(fontsize=9, loc="lower left")
    ax_acc.grid(alpha=0.2)

    # Budget failure annotation on encyclopedia
    enc = data["Encyclopedia"]
    for m in [200, 500]:
        trials = enc.get((condition, m))
        if trials:
            a = aggregate(trials)
            pct = a["budget_fails"] / a["n"] * 100
            ax_tok.annotate(f'{pct:.0f}% budget\nexhausted',
                           xy=(m, a["med_tokens"]),
                           xytext=(m * 1.5, a["med_tokens"] * 0.4),
                           fontsize=8, color="#d62728",
                           arrowprops=dict(arrowstyle="->", color="#d62728", lw=1))

    fig.suptitle(
        "Content familiarity disrupts retrieval: DEEP-INDEXED across three content types\n"
        "Shaded bands: interquartile range",
        fontsize=11,
    )
    plt.tight_layout()

    out = OUT_DIR / "fig5_content-comparison.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"Saved {out}")



if __name__ == "__main__":
    plot()
