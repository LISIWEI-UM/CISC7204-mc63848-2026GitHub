"""Rebuild the King County portfolio figures and numeric summary."""

import argparse
import hashlib
import io
import json
from pathlib import Path
from urllib.request import urlopen

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler


SOURCE = (
    "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/"
    "IBMDeveloperSkillsNetwork-DA0101EN-SkillsNetwork/labs/"
    "FinalModule_Coursera/data/kc_house_data_NaN.csv"
)
SHA256 = "6ce974df424ab9faf186f766a8fd93468ce7597767cb0df173889dcb3d2da928"
FEATURES = [
    "floors", "waterfront", "lat", "bedrooms", "sqft_basement", "view",
    "bathrooms", "sqft_living15", "sqft_above", "grade", "sqft_living",
]
INK = "#213743"
TEAL = "#14665f"
BLUE = "#30688b"


def load_sales(path):
    if path is None:
        with urlopen(SOURCE, timeout=60) as response:
            raw = response.read()
    else:
        raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA256:
        raise ValueError("The CSV differs from the course snapshot. Check the source and version.")
    return pd.read_csv(io.BytesIO(raw))


def style_axes(ax):
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#afbfc0")
    ax.tick_params(length=0, pad=7)


def plot_sizes(sales, path):
    groups = pd.qcut(sales["sqft_living"], 10)
    summary = sales.groupby(groups, observed=True).agg(
        area=("sqft_living", "median"),
        median=("price", "median"),
        lower=("price", lambda prices: prices.quantile(0.25)),
        upper=("price", lambda prices: prices.quantile(0.75)),
        sales=("price", "size"),
    )
    fig, ax = plt.subplots(figsize=(8, 4.8), layout="constrained")
    ax.fill_between(summary.area, summary.lower, summary.upper, color="#c5e1db",
                    label="Middle 50% of prices")
    ax.plot(summary.area, summary["median"], color=TEAL, marker="o", ms=5,
            linewidth=2.5, label="Median sale price")
    ax.set(xlabel="Median living area in each size group (sq ft)",
           ylabel="Sale price (USD)", ylim=(0, None))
    ax.set_title("Larger homes sold for more in King County", loc="left", pad=14)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"${y / 1e6:.1f}M"))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.grid(axis="y", color="#dfe8e7")
    ax.legend(frameon=False, loc="upper left")
    style_axes(ax)
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return summary


def compare_models(sales):
    train, test = train_test_split(sales, test_size=0.15, random_state=1)
    models = [
        ("Living area only", ["sqft_living"], LinearRegression()),
        ("11 features, linear Ridge", FEATURES,
         make_pipeline(SimpleImputer(), StandardScaler(), Ridge(alpha=0.1))),
        ("11 features, degree-2 Ridge", FEATURES,
         make_pipeline(SimpleImputer(), StandardScaler(),
                       PolynomialFeatures(degree=2, include_bias=False), Ridge(alpha=0.1))),
    ]
    scores = []
    for name, columns, model in models:
        model.fit(train[columns], train["price"])
        prediction = model.predict(test[columns])
        scores.append({
            "model": name,
            "test_r2": float(r2_score(test["price"], prediction)),
            "test_mae_usd": float(mean_absolute_error(test["price"], prediction)),
        })
    return scores, len(train), len(test), len(set(train["id"]) & set(test["id"]))


def plot_scores(scores, count, path):
    names = [score["model"] for score in scores]
    values = [score["test_r2"] for score in scores]
    fig, ax = plt.subplots(figsize=(8, 3.4), layout="constrained")
    bars = ax.barh(names, values, color=[BLUE, BLUE, TEAL], height=0.52)
    ax.bar_label(bars, fmt="%.3f", padding=6, weight="bold", color=INK)
    ax.set_title(f"Model fit on {count:,} held-out sales", loc="left", pad=16)
    ax.set(xlabel="Test R²", xlim=(0, 1))
    ax.invert_yaxis()
    ax.xaxis.set_major_locator(MaxNLocator(5))
    ax.grid(axis="x", color="#dfe8e7")
    style_axes(ax)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, help="Previously downloaded course CSV")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    sales = load_sales(args.csv)
    args.output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.size": 11, "axes.titlesize": 16, "axes.titleweight": "bold",
        "axes.labelcolor": INK, "text.color": INK, "xtick.color": INK,
        "ytick.color": INK, "axes.labelpad": 8, "legend.fontsize": 10,
    })
    groups = plot_sizes(sales, args.output / "price-by-living-area.png")
    scores, train_count, test_count, overlapping_ids = compare_models(sales)
    plot_scores(scores, test_count, args.output / "held-out-models.png")
    summary = {
        "input_sha256": SHA256,
        "sales": len(sales),
        "distinct_property_ids": int(sales["id"].nunique()),
        "first_sale": pd.to_datetime(sales["date"].min()).date().isoformat(),
        "last_sale": pd.to_datetime(sales["date"].max()).date().isoformat(),
        "train_sales": train_count,
        "test_sales": test_count,
        "property_ids_in_both_splits": overlapping_ids,
        "missing_feature_counts": {key: int(value) for key, value in
                                   sales[FEATURES].isna().sum().items() if value},
        "size_groups": groups.reset_index(drop=True).to_dict("records"),
        "models": scores,
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
