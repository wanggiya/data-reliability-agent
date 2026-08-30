from __future__ import annotations

from pathlib import Path

from .models import Finding, RepairAction, RepairProposal, RepairResult
from .profiler import load_table, write_table


def proposals_from_findings(findings: list[Finding]) -> list[RepairProposal]:
    proposals: list[RepairProposal] = []
    seen: set[str] = set()
    for finding in findings:
        evidence = finding.evidence
        proposal: RepairProposal | None = None
        if finding.finding_type == "duplicate_rows":
            proposal = RepairProposal(
                proposal_id="drop-exact-duplicates",
                action=RepairAction.drop_exact_duplicates,
                reason=evidence.detail,
                affected_count=evidence.count,
                risk="medium: repeated rows can occasionally be legitimate events",
            )
        elif finding.finding_type == "category_inconsistency" and evidence.column:
            proposal = RepairProposal(
                proposal_id=f"normalize-category-{evidence.column}",
                action=RepairAction.normalize_category_formatting,
                column=evidence.column,
                reason=evidence.detail,
                affected_count=evidence.count,
                risk="medium: trims whitespace and unifies case variants using the most frequent spelling",
            )
        elif finding.finding_type == "negative_values" and evidence.column:
            proposal = RepairProposal(
                proposal_id=f"null-negative-{evidence.column}",
                action=RepairAction.replace_negative_with_null,
                column=evidence.column,
                reason=evidence.detail,
                affected_count=evidence.count,
                risk="high: a negative value may be a valid correction or refund",
            )
        if proposal and proposal.proposal_id not in seen:
            proposals.append(proposal)
            seen.add(proposal.proposal_id)
    return proposals


def apply_approved_repairs(
    source_path: str | Path,
    output_path: str | Path,
    proposals: list[RepairProposal],
    approved_ids: set[str],
) -> RepairResult:
    if not approved_ids:
        raise ValueError("At least one proposal ID must be explicitly approved")
    known = {proposal.proposal_id for proposal in proposals}
    unknown = approved_ids - known
    if unknown:
        raise ValueError(f"Unknown proposal IDs: {sorted(unknown)}")
    source = Path(source_path).resolve()
    output = Path(output_path).resolve()
    if source == output:
        raise ValueError("Repairs must be written to a new file; source overwrite is forbidden")

    frame = load_table(source)
    before = len(frame)
    changes: list[str] = []
    for proposal in proposals:
        if proposal.proposal_id not in approved_ids:
            continue
        if proposal.action == RepairAction.drop_exact_duplicates:
            old = len(frame)
            frame = frame.drop_duplicates().reset_index(drop=True)
            changes.append(f"removed {old - len(frame)} exact duplicate rows")
        elif proposal.action == RepairAction.normalize_category_formatting and proposal.column:
            mask = frame[proposal.column].notna()
            before_values = frame.loc[mask, proposal.column].astype(str)
            trimmed = before_values.str.strip()
            normalized = trimmed.str.casefold()
            canonical: dict[str, str] = {}
            for key in normalized.unique():
                candidates = trimmed[normalized == key]
                canonical[key] = str(candidates.value_counts().index[0])
            after_values = normalized.map(canonical)
            changed = int((before_values != after_values).sum())
            frame.loc[mask, proposal.column] = after_values
            changes.append(f"normalized formatting in {changed} {proposal.column} values")
        elif proposal.action == RepairAction.replace_negative_with_null and proposal.column:
            mask = frame[proposal.column] < 0
            changed = int(mask.sum())
            frame.loc[mask, proposal.column] = None
            changes.append(f"replaced {changed} negative {proposal.column} values with null")
    write_table(frame, output)
    return RepairResult(
        source_path=str(source),
        output_path=str(output),
        approved_proposal_ids=sorted(approved_ids),
        rows_before=before,
        rows_after=len(frame),
        changes_applied=changes,
    )
