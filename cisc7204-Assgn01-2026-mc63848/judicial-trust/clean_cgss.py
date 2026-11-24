"""Reproduce the usable 2023 CGSS cleaning workflow in Python.

The original Stata files are read-only inputs. The caller supplies a private
output directory for datasets, logs and validation reports.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd



STANDARD_MISSING_COLUMNS = [
    "a2",
    "a4",
    "a5",
    "a6",
    "a7a",
    "a10",
    "a18",
    "a25a",
    "a33",
    "a34",
    "a35",
    "a36",
    "a43a",
    "a43e",
    "a44",
    "a611",
    "a612",
    "a613",
    "a614",
    "a64",
    "a65",
    "a66",
    "a42new",
    "a58",
    "a59a",
    "a59b",
    "a59j",
    "a59k",
]

INCOME_COLUMNS = ["a8a", "a8b", "a62"]

REQUIRED_COLUMNS = [
    "id",
    "s41",
    "s42",
    "s43",
    "a2",
    "a3a",
    "a7a",
    "a10",
    "a18",
    "a33",
    "a35",
    "a43a",
    "a44",
    "a58",
    "a59a",
    "a59b",
    "a59j",
    "a59k",
    "a611",
    "a612",
    "a64",
    "a8a",
    "a285",
    "c9b",
    "c9j",
    "c17p",
]

BASE_OUTPUT_COLUMNS = [
    "id",
    "s41",
    "s42",
    "s43",
    "trust_pomp",
    "trust_bin",
    "trust_c5",
    "trust_c7",
    "cohort",
    "female",
    "edu_years",
    "hukou",
    "party",
    "region",
    "subj_class",
    "econ_subj",
    "fairness",
    "social_trust",
    "si_med",
    "si_pen",
    "si_any",
    "empstat",
    "statsec",
    "contract",
    "lninc",
    "internet",
    "know_lawyer",
    "know_police",
    "voted",
    "year",
    "wt",
]

FINAL_OUTPUT_COLUMNS = BASE_OUTPUT_COLUMNS + ["wt_n", "incq", "s42c"]

INTENTIONAL_CORRECTIONS = {
    "internet": (
        "The Stata comments define a 1-5 scale, but the original script leaves "
        "negative nonresponse codes unchanged. Python converts them to missing."
    ),
    "know_lawyer": (
        "Only codes 1 (yes) and 2 (no) are valid. Telephone/inapplicable codes "
        "are missing instead of being treated as no."
    ),
    "know_police": (
        "Only codes 1 (yes) and 2 (no) are valid. Telephone/inapplicable codes "
        "are missing instead of being treated as no."
    ),
}


def _require_columns(df: pd.DataFrame, columns: Iterable[str]) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise KeyError(f"Raw CGSS2023 data are missing required columns: {missing}")


def _set_missing(
    df: pd.DataFrame,
    column: str,
    invalid: pd.Series,
    rule: str,
    log: list[dict[str, object]],
) -> None:
    invalid = invalid.fillna(False)
    changed = int((invalid & df[column].notna()).sum())
    missing_before = int(df[column].isna().sum())
    df.loc[invalid, column] = np.nan
    log.append(
        {
            "step": "set_missing",
            "variable": column,
            "rule": rule,
            "values_changed": changed,
            "missing_before": missing_before,
            "missing_after": int(df[column].isna().sum()),
        }
    )


def _binary(
    source: pd.Series, true_condition: pd.Series, valid: pd.Series | None = None
) -> pd.Series:
    if valid is None:
        valid = source.notna()
    result = pd.Series(np.nan, index=source.index, dtype="float64")
    result.loc[valid] = true_condition.loc[valid].astype("float64")
    return result


def clean_2023(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Clean the raw 2023 survey and return data plus a cleaning audit log."""
    _require_columns(raw, REQUIRED_COLUMNS)
    df = raw.copy()
    log: list[dict[str, object]] = []

    for column in STANDARD_MISSING_COLUMNS:
        if column in df.columns:
            _set_missing(
                df,
                column,
                (df[column] < 0) | df[column].isin([98, 99]),
                "negative values and codes 98/99 are missing",
                log,
            )

    for column in INCOME_COLUMNS:
        if column in df.columns:
            _set_missing(
                df,
                column,
                df[column].isin([9999995, 9999996, 9999997, 9999998, 9999999]),
                "income nonresponse codes 9999995-9999999 are missing",
                log,
            )

    _set_missing(
        df,
        "a3a",
        (df["a3a"] < 1900) | (df["a3a"] > 2023),
        "birth year must be between 1900 and 2023",
        log,
    )
    _set_missing(
        df,
        "c17p",
        (df["c17p"] < 1) | (df["c17p"] > 4),
        "judge-trust response must be between 1 and 4",
        log,
    )

    # Outcome: larger values indicate more trust.
    df["trust_pomp"] = (4 - df["c17p"]) / 3
    df["trust_bin"] = _binary(
        df["c17p"], df["c17p"].isin([1, 2]), valid=df["c17p"].notna()
    )
    df["trust_c5"] = df["trust_bin"]
    df["trust_c7"] = df["trust_bin"]

    df["female"] = _binary(df["a2"], df["a2"].eq(2))

    cohort = pd.Series(np.nan, index=df.index, dtype="float64")
    cohort.loc[df["a3a"].between(1900, 1949)] = 1
    cohort.loc[df["a3a"].between(1950, 1959)] = 2
    cohort.loc[df["a3a"].between(1960, 1969)] = 3
    cohort.loc[df["a3a"].between(1970, 1979)] = 4
    cohort.loc[df["a3a"].between(1980, 1989)] = 5
    cohort.loc[df["a3a"].between(1990, 2023)] = 6
    df["cohort"] = cohort

    education_years = {
        1: 0,
        2: 3,
        3: 6,
        4: 9,
        5: 12,
        6: 12,
        7: 12,
        8: 12,
        9: 15,
        10: 15,
        11: 16,
        12: 16,
        13: 19,
    }
    df["edu_years"] = df["a7a"].map(education_years).astype("float64")
    df["hukou"] = df["a18"].map({1: 1, 3: 1, 2: 2, 4: 2}).astype("float64")
    df["party"] = _binary(df["a10"], df["a10"].eq(4))

    east = [1, 4, 7, 10, 12, 15, 17, 19, 20, 24]
    central = [9, 11, 16, 18, 21, 22]
    west = [2, 3, 6, 8, 13, 14, 23, 25, 26, 28, 29, 30]
    northeast = [5, 27, 31]
    region = pd.Series(np.nan, index=df.index, dtype="float64")
    region.loc[df["s41"].isin(east)] = 1
    region.loc[df["s41"].isin(central)] = 2
    region.loc[df["s41"].isin(west)] = 3
    region.loc[df["s41"].isin(northeast)] = 4
    df["region"] = region

    df["subj_class"] = df["a43a"]
    df["econ_subj"] = df["a64"]
    df["fairness"] = df["a35"]
    df["social_trust"] = df["a33"]

    df["si_med"] = _binary(df["a611"], df["a611"].eq(1))
    df["si_pen"] = _binary(df["a612"], df["a612"].eq(1))
    social_insurance_valid = df["a611"].notna() & df["a612"].notna()
    df["si_any"] = _binary(
        df["a611"],
        df["a611"].eq(1) | df["a612"].eq(1),
        valid=social_insurance_valid,
    )

    empstat = pd.Series(np.nan, index=df.index, dtype="float64")
    empstat.loc[df["a58"].isin([2, 3])] = 1
    empstat.loc[df["a58"].eq(1) & df["a59a"].isin([3, 4, 5, 6, 7, 9])] = 2
    empstat.loc[df["a58"].eq(1) & df["a59a"].isin([1, 2, 8])] = 3
    empstat.loc[df["a58"].isin([4, 5, 6])] = 4
    df["empstat"] = empstat

    statsec = pd.Series(np.nan, index=df.index, dtype="float64")
    statsec.loc[df["a58"].eq(1) & df["a59j"].isin([1, 3, 6])] = 1
    statsec.loc[
        df["a58"].eq(1) & df["a59j"].eq(2) & df["a59k"].isin([1, 2])
    ] = 1
    statsec.loc[
        df["a58"].eq(1) & df["a59j"].eq(2) & df["a59k"].isin([3, 4, 5])
    ] = 0
    statsec.loc[df["a58"].eq(1) & df["a59j"].eq(5)] = 0
    df["statsec"] = statsec

    contract = pd.Series(np.nan, index=df.index, dtype="float64")
    contract.loc[df["empstat"].eq(2) & df["a59b"].isin([2, 3])] = 1
    contract.loc[df["empstat"].eq(2) & df["a59b"].eq(1)] = 0
    df["contract"] = contract

    valid_income = df["a8a"].notna() & df["a8a"].ge(0)
    df["lninc"] = np.nan
    df.loc[valid_income, "lninc"] = np.log(df.loc[valid_income, "a8a"] + 1)

    # Corrections to clear omissions in the Stata script.
    internet_valid = df["a285"].between(1, 5)
    df["internet"] = df["a285"].where(internet_valid).astype("float64")
    log.append(
        {
            "step": "derive",
            "variable": "internet",
            "rule": "valid scale is 1-5; all other codes are missing",
            "values_changed": int((df["a285"].notna() & ~internet_valid).sum()),
            "missing_before": int(df["a285"].isna().sum()),
            "missing_after": int(df["internet"].isna().sum()),
        }
    )

    lawyer_valid = df["c9b"].isin([1, 2])
    police_valid = df["c9j"].isin([1, 2])
    df["know_lawyer"] = _binary(df["c9b"], df["c9b"].eq(1), lawyer_valid)
    df["know_police"] = _binary(df["c9j"], df["c9j"].eq(1), police_valid)
    for source_column, output_column, valid in [
        ("c9b", "know_lawyer", lawyer_valid),
        ("c9j", "know_police", police_valid),
    ]:
        log.append(
            {
                "step": "derive",
                "variable": output_column,
                "rule": "1=yes, 2=no; telephone/inapplicable codes are missing",
                "values_changed": int((df[source_column].notna() & ~valid).sum()),
                "missing_before": int(df[source_column].isna().sum()),
                "missing_after": int(df[output_column].isna().sum()),
            }
        )

    df["voted"] = _binary(df["a44"], df["a44"].eq(1))
    df["year"] = 2023

    if "weight" in df.columns:
        df["wt"] = df["weight"].astype("float64")
        weight_rule = "copied from raw weight"
    else:
        df["wt"] = 1.0
        weight_rule = "raw file has no weight variable; use equal weight 1"
    log.append(
        {
            "step": "derive",
            "variable": "wt",
            "rule": weight_rule,
            "values_changed": len(df),
            "missing_before": 0,
            "missing_after": int(df["wt"].isna().sum()),
        }
    )

    output = df[BASE_OUTPUT_COLUMNS].copy()

    weight_sum = output["wt"].sum(min_count=1)
    if pd.isna(weight_sum) or weight_sum == 0:
        raise ValueError("Cannot normalize weights because their sum is missing or zero.")
    output["wt_n"] = output["wt"] * len(output) / weight_sum

    income_quintile = pd.Series(np.nan, index=output.index, dtype="float64")
    income_valid = output["lninc"].notna()
    income_quintile.loc[income_valid] = (
        pd.qcut(output.loc[income_valid, "lninc"], q=5, labels=False, duplicates="drop")
        .astype("float64")
        .add(1)
    )
    output["incq"] = income_quintile.fillna(0)
    output["s42c"] = output["s42"]

    return output[FINAL_OUTPUT_COLUMNS], pd.DataFrame(log)


def _compare_numeric(left: pd.Series, right: pd.Series) -> int:
    both_present = left.notna() & right.notna()
    if not both_present.any():
        return 0
    left_values = pd.to_numeric(left.loc[both_present], errors="coerce")
    right_values = pd.to_numeric(right.loc[both_present], errors="coerce")
    numeric = left_values.notna() & right_values.notna()
    mismatch = 0
    if numeric.any():
        mismatch += int(
            (~np.isclose(
                left_values.loc[numeric],
                right_values.loc[numeric],
                rtol=1e-6,
                atol=1e-6,
                equal_nan=True,
            )).sum()
        )
    nonnumeric = ~numeric
    if nonnumeric.any():
        mismatch += int(
            (left.loc[both_present].loc[nonnumeric].astype(str)
             != right.loc[both_present].loc[nonnumeric].astype(str)).sum()
        )
    return mismatch


def validate_against_reference(
    output: pd.DataFrame,
    reference: pd.DataFrame,
    reference_name: str,
    expected_differences: set[str],
) -> pd.DataFrame:
    """Compare by respondent id and summarize mismatches for each shared column."""
    left = output.set_index("id", drop=False).sort_index()
    right = reference.set_index("id", drop=False).sort_index()
    common_ids = left.index.intersection(right.index)
    rows: list[dict[str, object]] = []

    rows.append(
        {
            "reference": reference_name,
            "variable": "__rows__",
            "python_missing": len(right.index.difference(left.index)),
            "reference_missing": len(left.index.difference(right.index)),
            "value_mismatches": abs(len(left) - len(right)),
            "status": "PASS" if left.index.equals(right.index) else "FAIL",
            "note": "Row count and respondent-id coverage",
        }
    )

    for column in [column for column in output.columns if column in reference.columns]:
        left_column = left.loc[common_ids, column]
        right_column = right.loc[common_ids, column]
        python_missing = int(left_column.isna().sum())
        reference_missing = int(right_column.isna().sum())
        missing_mismatch = int((left_column.isna() ^ right_column.isna()).sum())
        value_mismatch = _compare_numeric(left_column, right_column)
        mismatch_total = missing_mismatch + value_mismatch

        if mismatch_total == 0:
            status = "PASS"
            note = ""
        elif column in expected_differences:
            status = "EXPECTED_DIFFERENCE"
            note = INTENTIONAL_CORRECTIONS.get(
                column,
                "Python preserves structurally missing trust outcomes; the pooled file uses zero.",
            )
        else:
            status = "FAIL"
            note = "Unexpected difference requiring review"

        rows.append(
            {
                "reference": reference_name,
                "variable": column,
                "python_missing": python_missing,
                "reference_missing": reference_missing,
                "value_mismatches": mismatch_total,
                "status": status,
                "note": note,
            }
        )

    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw-2023",
        type=Path,
        required=True,
        help="Path to the uncleaned CGSS2023 Stata file.",
    )
    parser.add_argument(
        "--reference-2023",
        type=Path,
        help="Optional Stata-cleaned 2023 file used only for validation.",
    )
    parser.add_argument(
        "--reference-2017",
        type=Path,
        help="Optional already-cleaned 2017 file to convert to CSV.",
    )
    parser.add_argument(
        "--pooled-reference",
        type=Path,
        help="Optional pooled Stata file used only for a secondary audit.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for generated CSV files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    raw = pd.read_stata(
        args.raw_2023, convert_categoricals=False, preserve_dtypes=True
    )
    cleaned, cleaning_log = clean_2023(raw)

    cleaned_path = args.output_dir / "CGSS2023_cleaned_python.csv"
    cleaned.to_csv(cleaned_path, index=False, encoding="utf-8-sig")
    cleaning_log.to_csv(
        args.output_dir / "cleaning_log_2023.csv", index=False, encoding="utf-8-sig"
    )

    validation_parts: list[pd.DataFrame] = []
    if args.reference_2023 is not None:
        reference_2023 = pd.read_stata(
            args.reference_2023,
            convert_categoricals=False,
            preserve_dtypes=False,
        )
        validation_parts.append(
            validate_against_reference(
                cleaned,
                reference_2023,
                "CGSS2023a.dta",
                set(INTENTIONAL_CORRECTIONS),
            )
        )

    if args.pooled_reference is not None:
        pooled = pd.read_stata(
            args.pooled_reference,
            convert_categoricals=False,
            preserve_dtypes=False,
        )
        pooled_2023 = pooled.loc[pooled["year"].eq(2023)].copy()
        validation_parts.append(
            validate_against_reference(
                cleaned,
                pooled_2023,
                "pooled_final.dta (2023 rows)",
                set(INTENTIONAL_CORRECTIONS)
                | {"trust_bin", "trust_c5", "trust_c7"},
            )
        )

    if validation_parts:
        validation = pd.concat(validation_parts, ignore_index=True)
        validation.to_csv(
            args.output_dir / "validation_report.csv",
            index=False,
            encoding="utf-8-sig",
        )
        unexpected_failures = validation[validation["status"].eq("FAIL")]
        if not unexpected_failures.empty:
            failed = unexpected_failures[["reference", "variable"]].to_dict("records")
            raise AssertionError(f"Unexpected validation differences: {failed}")

    if args.reference_2017 is not None:
        reference_2017 = pd.read_stata(
            args.reference_2017,
            convert_categoricals=False,
            preserve_dtypes=False,
        )
        reference_2017.to_csv(
            args.output_dir / "CGSS2017_cleaned_reference.csv",
            index=False,
            encoding="utf-8-sig",
        )

    print(f"Raw 2023 rows/columns: {raw.shape}")
    print(f"Cleaned 2023 rows/columns: {cleaned.shape}")
    print(f"Valid judge-trust responses: {int(cleaned['trust_bin'].notna().sum())}")
    print(f"Outputs: {args.output_dir}")


if __name__ == "__main__":
    main()
