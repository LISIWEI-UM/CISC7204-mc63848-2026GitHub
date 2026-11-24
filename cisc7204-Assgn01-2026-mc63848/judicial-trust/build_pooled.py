"""Append cleaned CGSS 2017 and 2023 data and reproduce final-work variables."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from clean_cgss import BASE_OUTPUT_COLUMNS


EXPECTED_REFERENCE_DIFFERENCES = {
    "trust_bin": "Python preserves missing trust responses instead of recoding them as 0.",
    "trust_c5": "Python preserves missing trust responses instead of recoding them as 0.",
    "trust_c7": "Python preserves missing trust responses instead of recoding them as 0.",
    "internet": "Invalid negative internet-use codes are missing in the Python data.",
    "know_lawyer": "Telephone/inapplicable responses are missing instead of being coded no.",
    "know_police": "Telephone/inapplicable responses are missing instead of being coded no.",
}


def require_columns(df: pd.DataFrame, columns: list[str], source: Path) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise KeyError(f"{source} is missing required columns: {missing}")


def build_pooled(data_2017: pd.DataFrame, data_2023: pd.DataFrame) -> pd.DataFrame:
    """Append the two years and create wt_n, incq, and s42c."""
    require_columns(data_2017, BASE_OUTPUT_COLUMNS, Path("2017 input"))
    require_columns(data_2023, BASE_OUTPUT_COLUMNS, Path("2023 input"))

    first = data_2017[BASE_OUTPUT_COLUMNS].copy()
    second = data_2023[BASE_OUTPUT_COLUMNS].copy()
    pooled = pd.concat([first, second], ignore_index=True)

    pooled["year"] = pd.to_numeric(pooled["year"], errors="raise").astype("int64")
    observed_years = set(pooled["year"].unique())
    if observed_years != {2017, 2023}:
        raise ValueError(f"Expected years 2017 and 2023, found {sorted(observed_years)}")

    if pooled.duplicated(["year", "id"]).any():
        duplicate_count = int(pooled.duplicated(["year", "id"]).sum())
        raise ValueError(f"Found {duplicate_count} duplicate year-id records.")

    year_n = pooled.groupby("year")["id"].transform("size")
    year_weight_sum = pooled.groupby("year")["wt"].transform("sum")
    if pooled["wt"].isna().any() or (year_weight_sum <= 0).any():
        raise ValueError("Weights must be present and have a positive sum within each year.")
    pooled["wt_n"] = pooled["wt"] * year_n / year_weight_sum

    pooled["incq"] = 0.0
    for _, indexes in pooled.groupby("year").groups.items():
        valid_indexes = pooled.loc[indexes].index[pooled.loc[indexes, "lninc"].notna()]
        pooled.loc[valid_indexes, "incq"] = (
            pd.qcut(
                pooled.loc[valid_indexes, "lninc"],
                q=5,
                labels=False,
                duplicates="drop",
            )
            .astype("float64")
            .add(1)
        )

    # Kept equivalent to final_work.do. A separate correction is advisable
    # before clustered regressions because all negative telephone codes coincide.
    pooled["s42c"] = pooled["s42"]
    return pooled[BASE_OUTPUT_COLUMNS + ["wt_n", "incq", "s42c"]]


def summarize(pooled: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for year, group in pooled.groupby("year", sort=True):
        valid = group["trust_bin"].notna() & group["wt_n"].notna()
        weighted_rate = (
            float(np.average(group.loc[valid, "trust_bin"], weights=group.loc[valid, "wt_n"]))
            if valid.any()
            else np.nan
        )
        rows.append(
            {
                "year": int(year),
                "rows": len(group),
                "valid_trust_responses": int(group["trust_bin"].notna().sum()),
                "missing_trust_responses": int(group["trust_bin"].isna().sum()),
                "weighted_trust_rate": weighted_rate,
                "normalized_weight_sum": float(group["wt_n"].sum()),
            }
        )
    return pd.DataFrame(rows)


def validate(pooled: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    """Compare the pooled result with the supplied Stata final dataset."""
    left = pooled.sort_values(["year", "id"]).reset_index(drop=True)
    right = reference.sort_values(["year", "id"]).reset_index(drop=True)
    rows: list[dict[str, object]] = []

    # Stata stores these keys as floats while Python keeps ``year`` as an
    # integer. Compare key values rather than requiring identical dtypes.
    same_keys = len(left) == len(right) and np.array_equal(
        left[["year", "id"]].to_numpy(dtype="float64"),
        right[["year", "id"]].to_numpy(dtype="float64"),
    )
    rows.append(
        {
            "variable": "__rows_and_keys__",
            "python_missing": 0,
            "reference_missing": 0,
            "mismatches": 0 if same_keys else abs(len(left) - len(right)) + 1,
            "status": "PASS" if same_keys else "FAIL",
            "note": "Row count and composite year-id keys",
        }
    )

    for column in [column for column in left.columns if column in right.columns]:
        python_values = left[column]
        reference_values = right[column]
        missing_mismatch = int(
            (python_values.isna() ^ reference_values.isna()).sum()
        )
        both_present = python_values.notna() & reference_values.notna()
        value_mismatch = 0
        if both_present.any():
            value_mismatch = int(
                (~np.isclose(
                    pd.to_numeric(python_values.loc[both_present], errors="coerce"),
                    pd.to_numeric(reference_values.loc[both_present], errors="coerce"),
                    rtol=1e-6,
                    atol=1e-6,
                    equal_nan=True,
                )).sum()
            )
        mismatch_total = missing_mismatch + value_mismatch

        if mismatch_total == 0:
            status = "PASS"
            note = ""
        elif column in EXPECTED_REFERENCE_DIFFERENCES:
            status = "EXPECTED_DIFFERENCE"
            note = EXPECTED_REFERENCE_DIFFERENCES[column]
        else:
            status = "FAIL"
            note = "Unexpected difference requiring review"

        rows.append(
            {
                "variable": column,
                "python_missing": int(python_values.isna().sum()),
                "reference_missing": int(reference_values.isna().sum()),
                "mismatches": mismatch_total,
                "status": status,
                "note": note,
            }
        )
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cleaned-2017",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--cleaned-2023",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--reference",
        type=Path,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_2017 = pd.read_csv(args.cleaned_2017)
    data_2023 = pd.read_csv(args.cleaned_2023)
    pooled = build_pooled(data_2017, data_2023)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    pooled_path = args.output_dir / "CGSS2017_2023_pooled_python.csv"
    pooled.to_csv(pooled_path, index=False, encoding="utf-8-sig")
    summarize(pooled).to_csv(
        args.output_dir / "pooled_summary.csv", index=False, encoding="utf-8-sig"
    )

    if args.reference is not None:
        reference = pd.read_stata(
            args.reference, convert_categoricals=False, preserve_dtypes=False
        )
        report = validate(pooled, reference)
        report.to_csv(
            args.output_dir / "pooled_validation_report.csv",
            index=False,
            encoding="utf-8-sig",
        )
        failures = report.loc[report["status"].eq("FAIL"), "variable"].tolist()
        if failures:
            raise AssertionError(f"Unexpected pooled-data differences: {failures}")

    print(f"Pooled rows/columns: {pooled.shape}")
    print(pooled.groupby("year").size().to_string())
    print(f"Output: {pooled_path}")


if __name__ == "__main__":
    main()
