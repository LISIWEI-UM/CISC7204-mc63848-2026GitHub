"""Create an unadjusted province-level judicial-trust scatter plot.

The x-axis is each province's raw 2017 judicial-trust rate and the y-axis is
its raw 2023 rate. Only provinces observed in both survey years are included.
No regression, control variables, or survey weights are used.
"""

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
import seaborn as sns


PROVINCE_NAMES = {
    1: "上海",
    2: "云南",
    3: "内蒙古",
    4: "北京",
    5: "吉林",
    6: "四川",
    7: "天津",
    8: "宁夏",
    9: "安徽",
    10: "山东",
    11: "山西",
    12: "广东",
    13: "广西",
    14: "新疆",
    15: "江苏",
    16: "江西",
    17: "河北",
    18: "河南",
    19: "浙江",
    20: "海南",
    21: "湖北",
    22: "湖南",
    23: "甘肃",
    24: "福建",
    25: "西藏",
    26: "贵州",
    27: "辽宁",
    28: "重庆",
    29: "陕西",
    30: "青海",
    31: "黑龙江",
}
REGION_NAMES = {1: "东部", 2: "中部", 3: "西部", 4: "东北"}
REGION_COLORS = {
    "东部": "#0072B2",
    "中部": "#D55E00",
    "西部": "#009E73",
    "东北": "#CC79A7",
}

# Offsets are in display points and keep nearby province labels readable.
LABEL_OFFSETS = {
    "上海": (8, -12),
    "云南": (-24, 9),
    "吉林": (-28, -13),
    "四川": (9, -12),
    "天津": (-28, -13),
    "安徽": (8, -13),
    "山西": (9, 7),
    "广西": (9, 8),
    "江西": (-30, 8),
    "河北": (-28, -13),
    "河南": (9, 8),
    "甘肃": (9, -13),
    "福建": (9, -13),
    "辽宁": (9, -13),
    "重庆": (9, 8),
    "青海": (9, 8),
}


def configure_chinese_font() -> None:
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


def calculate_province_rates(input_path: Path) -> tuple[pd.DataFrame, dict[int, int]]:
    data = pd.read_csv(input_path)
    required = {"year", "s41", "region", "trust_bin"}
    missing_columns = required.difference(data.columns)
    if missing_columns:
        raise ValueError(f"输入数据缺少必要变量：{sorted(missing_columns)}")

    analysis = data.dropna(subset=list(required)).copy()
    analysis = analysis.loc[
        analysis["year"].isin([2017, 2023])
        & analysis["s41"].isin(PROVINCE_NAMES)
        & analysis["region"].isin(REGION_NAMES)
        & analysis["trust_bin"].isin([0, 1])
    ].copy()
    analysis[["year", "s41", "region"]] = analysis[["year", "s41", "region"]].astype(int)

    coverage = analysis.groupby("year")["s41"].nunique().astype(int).to_dict()
    grouped = (
        analysis.groupby(["s41", "year"], as_index=False)
        .agg(n=("trust_bin", "size"), trust_rate=("trust_bin", "mean"))
    )
    rates = grouped.pivot(index="s41", columns="year", values=["n", "trust_rate"])
    rates = rates.dropna().copy()
    rates.columns = [f"{measure}_{int(year)}" for measure, year in rates.columns]
    rates = rates.reset_index()

    province_regions = analysis.groupby("s41")["region"].first().astype(int)
    rates["s41"] = rates["s41"].astype(int)
    rates["province"] = rates["s41"].map(PROVINCE_NAMES)
    rates["region_code"] = rates["s41"].map(province_regions)
    rates["region"] = rates["region_code"].map(REGION_NAMES)
    rates["n_2017"] = rates["n_2017"].astype(int)
    rates["n_2023"] = rates["n_2023"].astype(int)
    rates["change_pp"] = (rates["trust_rate_2023"] - rates["trust_rate_2017"]) * 100
    return rates.sort_values("s41").reset_index(drop=True), coverage


def draw_scatter(
    rates: pd.DataFrame,
    coverage: dict[int, int],
    output_path: Path,
) -> None:
    sns.set_theme(style="whitegrid", context="talk", font_scale=0.90)
    configure_chinese_font()

    figure, axis = plt.subplots(figsize=(9.6, 9.1))
    sns.scatterplot(
        data=rates,
        x="trust_rate_2017",
        y="trust_rate_2023",
        hue="region",
        hue_order=list(REGION_COLORS),
        palette=REGION_COLORS,
        s=125,
        edgecolor="white",
        linewidth=1.2,
        alpha=0.95,
        ax=axis,
        zorder=3,
    )

    plotted = rates[["trust_rate_2017", "trust_rate_2023"]].to_numpy()
    lower_limit = max(0.0, np.floor((plotted.min() - 0.03) * 10) / 10)
    upper_limit = min(1.0, np.ceil((plotted.max() + 0.03) * 10) / 10)
    axis.plot(
        [lower_limit, upper_limit],
        [lower_limit, upper_limit],
        linestyle="--",
        color="#777777",
        linewidth=1.4,
        label="45度参考线",
        zorder=1,
    )

    for row in rates.itertuples(index=False):
        offset = LABEL_OFFSETS.get(row.province, (8, 6))
        axis.annotate(
            row.province,
            xy=(row.trust_rate_2017, row.trust_rate_2023),
            xytext=offset,
            textcoords="offset points",
            ha="left" if offset[0] >= 0 else "right",
            va="center",
            fontsize=9.5,
            color="#2F2F2F",
            bbox={
                "boxstyle": "round,pad=0.12",
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.72,
            },
            zorder=4,
        )

    axis.text(
        0.05,
        0.17,
        "线上方：2023年信任率更高",
        fontsize=10.5,
        color="#555555",
        rotation=45,
        transform=axis.transAxes,
        ha="left",
        va="bottom",
    )
    axis.set_xlim(lower_limit, upper_limit)
    axis.set_ylim(lower_limit, upper_limit)
    axis.set_aspect("equal", adjustable="box")
    axis.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    axis.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    axis.set_xlabel("2017年原始司法信任率", labelpad=12)
    axis.set_ylabel("2023年原始司法信任率", labelpad=12)
    axis.grid(color="#D9D9D9", linewidth=0.8, alpha=0.8)
    sns.despine(ax=axis, left=False, bottom=False)

    handles, labels = axis.get_legend_handles_labels()
    axis.legend(
        handles,
        labels,
        title="地区",
        frameon=False,
        loc="lower right",
        borderaxespad=0.8,
    )

    figure.suptitle(
        "各省司法信任率：2017与2023年比较",
        fontsize=19,
        fontweight="bold",
        y=0.975,
    )
    axis.set_title(
        f"两年共同覆盖的{len(rates)}个省级地区",
        fontsize=12,
        color="#555555",
        pad=14,
    )

    figure.subplots_adjust(left=0.13, right=0.96, bottom=0.10, top=0.88)
    figure.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rates, coverage = calculate_province_rates(args.input)

    table_path = args.output_dir / "regional_judicial_trust_rates.csv"
    figure_path = args.output_dir / "regional_judicial_trust_scatter.png"
    rates.to_csv(table_path, index=False, encoding="utf-8-sig")
    draw_scatter(rates, coverage, figure_path)

    print(rates.to_string(index=False))
    print(f"\nSaved regional table:   {table_path}")
    print(f"Saved regional scatter: {figure_path}")


if __name__ == "__main__":
    main()
