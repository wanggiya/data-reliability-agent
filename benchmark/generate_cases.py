from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).parent
CASES = ROOT / "cases"


def base() -> pd.DataFrame:
    return pd.DataFrame({
        "record_id": range(1, 9),
        "month": pd.date_range("2026-01-01", periods=8, freq="MS").strftime("%Y-%m-%d"),
        "region": ["North", "South", "East", "West", "North", "South", "East", "West"],
        "cases": [10, 12, 11, 15, 13, 14, 16, 18],
        "revenue": [100, 120, 110, 150, 130, 140, 160, 180],
    })


def main() -> None:
    CASES.mkdir(parents=True, exist_ok=True)
    cases: list[dict[str, object]] = []
    clean = base()
    clean.to_csv(CASES / "case_01_clean.csv", index=False)
    cases.append({"file": "case_01_clean.csv", "expected": []})

    missing = base(); missing.loc[2, "revenue"] = None
    missing.to_csv(CASES / "case_02_missing.csv", index=False)
    cases.append({"file": "case_02_missing.csv", "expected": ["missing_values"]})

    duplicate = pd.concat([base(), base().iloc[[2]]], ignore_index=True)
    duplicate.to_csv(CASES / "case_03_duplicate.csv", index=False)
    cases.append({"file": "case_03_duplicate.csv", "expected": ["duplicate_rows", "duplicate_ids"]})

    category = base(); category.loc[4, "region"] = " north "
    category.to_csv(CASES / "case_04_category.csv", index=False)
    cases.append({"file": "case_04_category.csv", "expected": ["category_inconsistency"]})

    dates = base().drop(index=3).reset_index(drop=True)
    dates.to_csv(CASES / "case_05_date_gap.csv", index=False)
    cases.append({"file": "case_05_date_gap.csv", "expected": ["date_gaps"]})

    multi = base(); multi.loc[1, "revenue"] = -5; multi.loc[6, "cases"] = 5000; multi.loc[3, "region"] = "WEST "
    multi["unused_metric"] = 0
    multi.to_csv(CASES / "case_06_multi_issue.csv", index=False)
    cases.append({"file": "case_06_multi_issue.csv", "expected": ["negative_values", "numeric_outliers", "category_inconsistency", "suspicious_zeros"]})

    (ROOT / "expected_findings.json").write_text(json.dumps({"cases": cases}, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(cases)} benchmark cases in {CASES}")


if __name__ == "__main__":
    main()

