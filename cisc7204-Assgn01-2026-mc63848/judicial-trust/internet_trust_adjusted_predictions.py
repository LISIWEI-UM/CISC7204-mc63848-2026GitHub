"""Plot M2-adjusted judicial-trust probabilities by internet-use frequency."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd
from scipy.stats import t as student_t
import seaborn as sns


INTERNET_LABELS = {
    1: "从不",
    2: "很少",
    3: "有时",
    4: "经常",
    5: "非常频繁",
}
CONTINUOUS = ["female", "edu_years", "party", "econ_subj", "si_any", "internet"]
CATEGORICAL = ["year", "cohort", "hukou", "region", "incq", "empstat"]


def configure_chinese_font() -> None:
    """Choose an installed Chinese font while retaining portable fallbacks."""
    installed = {font.name for font in font_manager.fontManager.ttflist}
    candidates = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "Arial Unicode MS",
    ]
    selected = next((name for name in candidates if name in installed), "DejaVu Sans")
    plt.rcParams["font.sans-serif"] = [selected, "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def prepare_m2_sample(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Create the complete-case M2 design matrix and aligned model inputs."""
    required = ["trust_bin", "wt_n", "s42c", *CONTINUOUS, *CATEGORICAL]
    missing = set(required).difference(data.columns)
    if missing:
        raise ValueError(f"输入数据缺少必要变量：{sorted(missing)}")

    sample = data.dropna(subset=required).copy()
    sample = sample.loc[
        sample["trust_bin"].isin([0, 1])
        & sample["internet"].between(1, 5)
        & sample["wt_n"].gt(0)
    ].copy()

    numeric = sample[CONTINUOUS].astype(float)
    categorical = pd.get_dummies(
        sample[CATEGORICAL].astype(int).astype(str),
        prefix=CATEGORICAL,
        drop_first=True,
        dtype=float,
    )
    design = pd.concat([numeric, categorical], axis=1)
    design.insert(0, "constant", 1.0)
    return (
        design,
        sample["trust_bin"].astype(float),
        sample["wt_n"].astype(float),
        sample["s42c"].astype(str),
    )


def fit_m2(
    design: pd.DataFrame,
    outcome: pd.Series,
    weights: pd.Series,
    clusters: pd.Series,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Fit weighted LPM M2 with finite-sample-corrected cluster covariance."""
    x = design.to_numpy(dtype=float)
    y = outcome.to_numpy(dtype=float)
    w = weights.to_numpy(dtype=float)

    bread = np.linalg.pinv(x.T @ (w[:, None] * x))
    beta = bread @ (x.T @ (w * y))
    residual = y - x @ beta
    scores = x * (w * residual)[:, None]

    cluster_codes, unique_clusters = pd.factorize(clusters, sort=False)
    cluster_scores = np.zeros((len(unique_clusters), x.shape[1]), dtype=float)
    np.add.at(cluster_scores, cluster_codes, scores)
    meat = cluster_scores.T @ cluster_scores

    n_observations, n_parameters = x.shape
    n_clusters = len(unique_clusters)
    correction = (n_clusters / (n_clusters - 1)) * (
        (n_observations - 1) / (n_observations - n_parameters)
    )
    covariance = correction * bread @ meat @ bread
    return beta, covariance, n_clusters


def adjusted_predictions(
    design: pd.DataFrame,
    weights: pd.Series,
    beta: np.ndarray,
    covariance: np.ndarray,
    n_clusters: int,
) -> pd.DataFrame:
    """Average M2 predictions after setting everyone to each internet-use level."""
    critical_value = float(student_t.ppf(0.975, n_clusters - 1))
    rows: list[dict[str, float | int | str]] = []
    for level, label in INTERNET_LABELS.items():
        scenario = design.copy()
        scenario["internet"] = float(level)
        average_design = np.average(
            scenario.to_numpy(dtype=float),
            axis=0,
            weights=weights.to_numpy(dtype=float),
        )
        prediction = float(average_design @ beta)
        standard_error = float(np.sqrt(max(average_design @ covariance @ average_design, 0.0)))
        rows.append(
            {
                "internet_level": level,
                "internet_label": label,
                "adjusted_probability": prediction,
                "standard_error": standard_error,
                "ci_low": prediction - critical_value * standard_error,
                "ci_high": prediction + critical_value * standard_error,
            }
        )
    return pd.DataFrame(rows)


def draw_figure(predictions: pd.DataFrame, output_path: Path) -> None:
    """Create the adjusted-probability line chart."""
    sns.set_theme(style="whitegrid", context="talk", font_scale=0.92)
    configure_chinese_font()

    x = predictions["internet_level"].to_numpy(dtype=float)
    y = predictions["adjusted_probability"].to_numpy(dtype=float)
    lower_error = y - predictions["ci_low"].to_numpy(dtype=float)
    upper_error = predictions["ci_high"].to_numpy(dtype=float) - y

    figure, axis = plt.subplots(figsize=(11.4, 7.1))
    axis.plot(
        x,
        y,
        color="#0072B2",
        marker="o",
        markersize=10,
        linewidth=2.8,
        zorder=3,
    )
    axis.errorbar(
        x,
        y,
        yerr=np.vstack([lower_error, upper_error]),
        fmt="none",
        ecolor="#0072B2",
        elinewidth=1.7,
        capsize=5,
        capthick=1.7,
        alpha=0.9,
        zorder=2,
    )
    for x_value, probability in zip(x, y, strict=True):
        axis.text(
            x_value,
            probability + 0.006,
            f"{probability:.1%}",
            ha="center",
            va="bottom",
            fontsize=11,
            color="#005A8D",
            fontweight="semibold",
        )

    figure.suptitle(
        "互联网使用频率与调整后的司法信任率",
        fontsize=20,
        fontweight="bold",
        y=0.965,
    )
    axis.set_title(
        "基于M2加权线性概率模型的预测值及95%置信区间",
        fontsize=12.5,
        color="#555555",
        pad=15,
    )
    axis.set_xticks(list(INTERNET_LABELS))
    axis.set_xticklabels(list(INTERNET_LABELS.values()))
    axis.set_xlabel("互联网使用频率", labelpad=11)
    axis.set_ylabel("调整后的司法信任概率", labelpad=11)
    axis.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    padding = 0.025
    axis.set_ylim(
        max(0.0, float(predictions["ci_low"].min()) - padding),
        min(1.0, float(predictions["ci_high"].max()) + padding),
    )
    axis.grid(axis="x", visible=False)
    axis.grid(axis="y", color="#D9D9D9", linewidth=0.8, alpha=0.8)
    sns.despine(ax=axis, left=False, bottom=False)
    figure.subplots_adjust(left=0.13, right=0.98, bottom=0.15, top=0.83)
    figure.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(args.input)
    design, outcome, weights, clusters = prepare_m2_sample(data)
    beta, covariance, n_clusters = fit_m2(design, outcome, weights, clusters)
    predictions = adjusted_predictions(design, weights, beta, covariance, n_clusters)
    predictions["n"] = len(outcome)
    predictions["clusters"] = n_clusters

    summary_path = args.output_dir / "internet_trust_m2_adjusted_predictions.csv"
    figure_path = args.output_dir / "internet_trust_m2_adjusted_predictions.png"
    predictions.to_csv(summary_path, index=False, encoding="utf-8-sig")
    draw_figure(predictions, figure_path)

    internet_position = design.columns.get_loc("internet")
    print(predictions.to_string(index=False))
    print(f"\nM2 internet coefficient: {beta[internet_position]:.6f}")
    print(f"Saved summary: {summary_path}")
    print(f"Saved figure:  {figure_path}")


if __name__ == "__main__":
    main()
