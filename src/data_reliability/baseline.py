from __future__ import annotations

from pathlib import Path

from .models import Evidence
from .profiler import profile_dataset


def run_baseline(path: str | Path) -> list[Evidence]:
    """A reasonable basic script: report missing cells and exact duplicate rows."""
    frame, _ = profile_dataset(path)
    findings: list[Evidence] = []
    for column, count in frame.isna().sum().items():
        if count:
            findings.append(Evidence(check="missing_values", finding_type="missing_values", column=column, count=int(count), detail=f"{count} missing values in {column}"))
    duplicates = int(frame.duplicated(keep=False).sum())
    if duplicates:
        findings.append(Evidence(check="duplicate_rows", finding_type="duplicate_rows", count=duplicates, detail=f"{duplicates} rows participate in exact duplicates"))
    return findings

