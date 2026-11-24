"""Draw the coding guide or rebuild both descriptive analyses with local data."""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
ECON = ["Far below average", "Below average", "Average", "Above average", "Far above average"]
COHORT = ["1949 or earlier", "1950s", "1960s", "1970s", "1980s", "1990 or later"]
TABLE = "group-estimates.csv"


def summarize_pooled(path):
    """Use only the five harmonized columns needed for these two group summaries."""
    data = pd.read_csv(path, usecols=["year", "econ_subj", "cohort", "trust_bin", "wt_n"])
    responses = data[data.year.isin([2017, 2023]) & data.trust_bin.isin([0, 1])]
    rows = []
    for (year, code), group in responses.groupby(["year", "econ_subj"]):
        if code not in range(1, len(ECON) + 1):
            continue
        group = group[group.wt_n.gt(0) & np.isfinite(group.wt_n)]
        weights = group.wt_n
        n = len(group)
        if not n:
            continue
        rate = np.average(group.trust_bin, weights=weights)
        effective_n = weights.sum() ** 2 / (weights**2).sum()
        half_width = 1.96 * np.sqrt(rate * (1 - rate) / effective_n)
        rows.append(["economic status", year, ECON[int(code) - 1], n, rate,
                     max(0, rate - half_width), min(1, rate + half_width)])

    for (year, code), group in responses.groupby(["year", "cohort"]):
        if code not in range(1, len(COHORT) + 1):
            continue
        n = len(group)
        rate = group.trust_bin.mean()
        z = 1.96
        denominator = 1 + z**2 / n
        center = (rate + z**2 / (2 * n)) / denominator
        half_width = z * np.sqrt(rate * (1 - rate) / n + z**2 / (4 * n**2)) / denominator
        rows.append(["birth cohort", year, COHORT[int(code) - 1], n, rate,
                     max(0, center - half_width), min(1, center + half_width)])
    return pd.DataFrame(rows, columns=["comparison", "year", "group", "n",
                                       "proportion", "lower_95", "upper_95"])


def draw(table, comparison, groups, path, title, xlabel):
    fig, ax = plt.subplots(figsize=(8.1, 2.2 + 0.46 * len(groups)), layout="constrained")
    selected = table[table.comparison == comparison]
    y = np.arange(len(groups))
    for year, label, offset, color, marker in [
        (2017, "2017 · courts", -0.11, "#22637d", "o"),
        (2023, "2023 · judges", 0.11, "#a85122", "s"),
    ]:
        points = selected[selected.year == year].set_index("group").reindex(groups)
        rate = points.proportion
        errors = np.array([rate - points.lower_95, points.upper_95 - rate])
        ax.errorbar(rate, y + offset, xerr=errors, label=label, fmt=marker,
                    color=color, ms=6, lw=1.5, capsize=3, zorder=3)

    ax.set_yticks(y, groups)
    ax.set_ylim(len(groups) - 0.55, -0.55)
    ax.set_xlim(0.0, 1.0)
    ax.set_xticks(np.arange(0.0, 1.01, 0.1))
    ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.set_xlabel(xlabel, labelpad=8)
    ax.set_title(title, loc="left", pad=38, fontsize=17, weight="bold", color="#203c49")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.005), borderaxespad=0,
              frameon=False, ncol=2, handlelength=1.5)
    ax.grid(axis="x", color="#dce6e7")
    ax.tick_params(length=0, pad=6, labelsize=11)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#a4b6b8")
    fig.savefig(path, dpi=160)
    plt.close(fig)


def draw_coding(path):
    """Visualize the two coding rules directly, using no survey records."""
    fig, axes = plt.subplots(2, figsize=(8.5, 4.4))
    fig.subplots_adjust(left=0.045, right=0.96, bottom=0.20, top=0.74, hspace=0.9)
    fig.text(0.045, 0.94, "How two survey items become one indicator",
             fontsize=20, weight="bold", color="#203c49", va="top")
    fig.text(0.045, 0.83, "Response codes for trust in courts (2017) and judges (2023)",
             fontsize=11, color="#40535e", va="top")
    for ax, label, codes, positive in [
        (axes[0], "2017    Courts", range(11), set(range(6, 11))),
        (axes[1], "2023    Judges", range(1, 5), {1, 2}),
    ]:
        ax.set_title(label, loc="left", fontsize=13, weight="bold", color="#203c49", pad=3)
        ax.set(xlim=(-0.5, 10.5), ylim=(0, 1))
        ax.axis("off")
        for x, code in enumerate(codes):
            yes = code in positive
            ax.bar(x, 0.90, width=0.93, color="#21695f" if yes else "#e0e9eb")
            ax.text(x, 0.45, str(code), ha="center", va="center", weight="bold",
                    color="white" if yes else "#253f49", fontsize=12)
    fig.text(0.045, 0.115, "Green = meets trust threshold", fontsize=11,
             color="#21695f", weight="bold")
    fig.text(0.51, 0.115, "Gray = below threshold", fontsize=11, color="#3c535a")
    fig.text(0.045, 0.045, "Missing and inapplicable responses are excluded from the denominator.",
             fontsize=10.5, color="#40535e")
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pooled", type=Path, help="Local authorized, harmonized CSV")
    parser.add_argument("--output", type=Path, help="Output directory (private for pooled data)")
    args = parser.parse_args()
    if args.pooled is None:
        figures = (args.output or ROOT) / "figures"
        figures.mkdir(parents=True, exist_ok=True)
        draw_coding(figures / "trust-coding.png")
        return
    if args.output is None:
        parser.error("Supply --output with a private directory for the survey analysis.")
    args.output.mkdir(parents=True, exist_ok=True)
    table_path = args.output / TABLE
    summarize_pooled(args.pooled).to_csv(table_path, index=False, float_format="%.8f")
    table = pd.read_csv(table_path)
    figures = args.output / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    draw(table, "economic status", ECON, figures / "trust-by-economic-status.png",
         "Reported trust by household economic standing",
         "Share meeting the trust threshold (within-year weights)")
    draw(table, "birth cohort", COHORT, figures / "trust-by-birth-cohort.png",
         "Reported trust by birth cohort",
         "Share meeting the trust threshold (unweighted)")


if __name__ == "__main__":
    main()
