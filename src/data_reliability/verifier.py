from __future__ import annotations

from .models import Evidence, Finding, Severity, VerificationSummary


CRITICAL_TYPES = {"duplicate_ids", "negative_values", "total_reconciliation"}


def verify_evidence(items: list[Evidence]) -> tuple[list[Finding], VerificationSummary]:
    accepted: list[Finding] = []
    rejected: list[str] = []
    seen: set[tuple[str, str | None, str]] = set()
    for evidence in items:
        key = (evidence.finding_type, evidence.column, evidence.detail)
        if key in seen:
            rejected.append(f"duplicate evidence: {evidence.detail}")
            continue
        seen.add(key)
        if evidence.count <= 0:
            rejected.append(f"non-positive evidence count: {evidence.detail}")
            continue
        if evidence.row_indices and len(evidence.row_indices) > evidence.count:
            rejected.append(f"row evidence exceeds count: {evidence.detail}")
            continue
        severity = Severity.critical if evidence.finding_type in CRITICAL_TYPES else Severity.warning
        accepted.append(Finding(
            finding_type=evidence.finding_type,
            severity=severity,
            title=evidence.finding_type.replace("_", " ").title(),
            detail=evidence.detail,
            evidence=evidence,
            verified=True,
        ))
    return accepted, VerificationSummary(accepted=len(accepted), rejected=len(rejected), rejected_reasons=rejected)

