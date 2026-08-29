from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Severity(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class CheckName(str, Enum):
    missing_values = "missing_values"
    duplicate_rows = "duplicate_rows"
    duplicate_ids = "duplicate_ids"
    numeric_outliers = "numeric_outliers"
    negative_values = "negative_values"
    suspicious_zeros = "suspicious_zeros"
    category_inconsistency = "category_inconsistency"
    date_gaps = "date_gaps"
    total_reconciliation = "total_reconciliation"


class DatasetProfile(BaseModel):
    path: str
    rows: int
    columns: int
    column_names: list[str]
    dtypes: dict[str, str]
    null_counts: dict[str, int]
    sample: list[dict[str, Any]]
    numeric_columns: list[str]
    date_candidates: list[str]
    id_candidates: list[str]


class InvestigationPlan(BaseModel):
    goal: str
    checks: list[CheckName]
    rationale: dict[str, str] = Field(default_factory=dict)
    source: str = "deterministic"


class Evidence(BaseModel):
    check: CheckName
    finding_type: str
    column: str | None = None
    count: int = 0
    row_indices: list[int] = Field(default_factory=list)
    values: list[Any] = Field(default_factory=list)
    detail: str


class Finding(BaseModel):
    finding_type: str
    severity: Severity
    title: str
    detail: str
    evidence: Evidence
    verified: bool = False


class VerificationSummary(BaseModel):
    accepted: int
    rejected: int
    rejected_reasons: list[str] = Field(default_factory=list)


class RunResult(BaseModel):
    run_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    profile: DatasetProfile
    plan: InvestigationPlan
    findings: list[Finding]
    verification: VerificationSummary
    report_path: str | None = None
    trajectory_path: str | None = None

