from __future__ import annotations

import re

import pandas as pd

from .models import CheckName, DatasetProfile, Evidence


def _indices(mask: pd.Series, limit: int = 20) -> list[int]:
    return [int(i) for i in mask[mask].index[:limit]]


def run_check(name: CheckName, frame: pd.DataFrame, profile: DatasetProfile) -> list[Evidence]:
    findings: list[Evidence] = []
    if name == CheckName.missing_values:
        for column, count in frame.isna().sum().items():
            if count:
                mask = frame[column].isna()
                findings.append(Evidence(check=name, finding_type="missing_values", column=column, count=int(count), row_indices=_indices(mask), detail=f"{count} missing values in {column}"))

    elif name == CheckName.duplicate_rows:
        mask = frame.duplicated(keep=False)
        if mask.any():
            findings.append(Evidence(check=name, finding_type="duplicate_rows", count=int(mask.sum()), row_indices=_indices(mask), detail=f"{int(mask.sum())} rows participate in exact duplicates"))

    elif name == CheckName.duplicate_ids:
        for column in profile.id_candidates:
            mask = frame[column].notna() & frame[column].duplicated(keep=False)
            if mask.any():
                values = frame.loc[mask, column].astype(str).unique()[:10].tolist()
                findings.append(Evidence(check=name, finding_type="duplicate_ids", column=column, count=int(mask.sum()), row_indices=_indices(mask), values=values, detail=f"{int(mask.sum())} rows contain duplicated {column} values"))

    elif name == CheckName.negative_values:
        for column in profile.numeric_columns:
            if re.search(r"count|amount|total|revenue|cases|quantity|population", column, re.I):
                mask = frame[column] < 0
                if mask.any():
                    findings.append(Evidence(check=name, finding_type="negative_values", column=column, count=int(mask.sum()), row_indices=_indices(mask), values=frame.loc[mask, column].head(10).tolist(), detail=f"{int(mask.sum())} negative values in non-negative measure {column}"))

    elif name == CheckName.suspicious_zeros:
        for column in profile.numeric_columns:
            count = int((frame[column] == 0).sum())
            if len(frame) >= 5 and count / len(frame) >= 0.8:
                findings.append(Evidence(check=name, finding_type="suspicious_zeros", column=column, count=count, detail=f"{count}/{len(frame)} values in {column} are zero"))

    elif name == CheckName.numeric_outliers:
        for column in profile.numeric_columns:
            values = frame[column].dropna()
            if len(values) < 5 or values.nunique() < 4:
                continue
            q1, q3 = values.quantile([0.25, 0.75])
            iqr = q3 - q1
            if iqr == 0:
                continue
            mask = (frame[column] < q1 - 3 * iqr) | (frame[column] > q3 + 3 * iqr)
            if mask.any():
                findings.append(Evidence(check=name, finding_type="numeric_outliers", column=column, count=int(mask.sum()), row_indices=_indices(mask), values=frame.loc[mask, column].head(10).tolist(), detail=f"{int(mask.sum())} extreme IQR outliers in {column}"))

    elif name == CheckName.category_inconsistency:
        for column in frame.select_dtypes(include="object").columns:
            clean = frame[column].dropna().astype(str)
            normalized = clean.str.strip().str.casefold()
            if clean.nunique() > normalized.nunique():
                variants: dict[str, list[str]] = {}
                for original, norm in zip(clean, normalized):
                    variants.setdefault(norm, [])
                    if original not in variants[norm]:
                        variants[norm].append(original)
                collisions = [v for v in variants.values() if len(v) > 1]
                findings.append(Evidence(check=name, finding_type="category_inconsistency", column=column, count=sum(len(v) for v in collisions), values=collisions[:10], detail=f"Formatting variants represent the same normalized category in {column}"))

    elif name == CheckName.date_gaps:
        for column in profile.date_candidates:
            parsed = pd.to_datetime(frame[column], errors="coerce")
            dates = parsed.dropna().sort_values().drop_duplicates()
            if len(dates) >= 3:
                periods = dates.dt.to_period("M")
                expected = pd.period_range(periods.min(), periods.max(), freq="M")
                missing = expected.difference(periods)
                if len(missing):
                    findings.append(Evidence(check=name, finding_type="date_gaps", column=column, count=len(missing), values=[str(v) for v in missing[:12]], detail=f"{len(missing)} monthly periods are missing in {column}"))

    elif name == CheckName.total_reconciliation:
        total_columns = [c for c in frame.columns if c.lower() == "total"]
        components = [c for c in profile.numeric_columns if c not in total_columns]
        for total in total_columns:
            if len(components) >= 2:
                delta = frame[components].sum(axis=1) - frame[total]
                mask = delta.abs() > 1e-9
                if mask.any():
                    findings.append(Evidence(check=name, finding_type="total_reconciliation", column=total, count=int(mask.sum()), row_indices=_indices(mask), values=delta[mask].head(10).tolist(), detail=f"{int(mask.sum())} rows do not reconcile: total differs from numeric component sum"))
    return findings


def execute_plan(checks: list[CheckName], frame: pd.DataFrame, profile: DatasetProfile) -> list[Evidence]:
    evidence: list[Evidence] = []
    for check in checks:
        evidence.extend(run_check(check, frame, profile))
    return evidence

