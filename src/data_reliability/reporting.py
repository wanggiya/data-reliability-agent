from __future__ import annotations

from pathlib import Path

from .models import RunResult


def write_markdown(result: RunResult, path: Path) -> Path:
    lines = [
        "# Data Reliability Investigation",
        "",
        f"- Run: `{result.run_id}`",
        f"- Dataset: `{result.profile.path}`",
        f"- Shape: {result.profile.rows} rows × {result.profile.columns} columns",
        f"- Planning source: `{result.plan.source}`",
        f"- Goal: {result.plan.goal}",
        "",
        "## Investigation plan",
        "",
    ]
    lines.extend(f"- `{check.value}` — {result.plan.rationale.get(check.value, 'Selected by investigator')}" for check in result.plan.checks)
    lines.extend(["", "## Verified findings", ""])
    if not result.findings:
        lines.append("No supported problems were detected by the selected checks.")
    for index, finding in enumerate(result.findings, 1):
        lines.extend([
            f"### {index}. {finding.title} ({finding.severity.value})",
            "",
            finding.detail,
            "",
            f"Evidence: check=`{finding.evidence.check.value}`, column=`{finding.evidence.column}`, count={finding.evidence.count}, rows={finding.evidence.row_indices}, values={finding.evidence.values}",
            "",
        ])
    lines.extend([
        "## Verification",
        "",
        f"- Accepted findings: {result.verification.accepted}",
        f"- Rejected unsupported findings: {result.verification.rejected}",
        "",
        "## Proposed repairs — approval required",
        "",
    ])
    if not result.repair_proposals:
        lines.append("No bounded automatic repair is proposed for these findings.")
    for proposal in result.repair_proposals:
        lines.append(f"- `{proposal.proposal_id}`: {proposal.action.value}; affected≈{proposal.affected_count}; risk={proposal.risk}")
    lines.extend([
        "",
        "## Safety note",
        "",
        "Investigation is read-only. Repairs require explicit proposal IDs, never overwrite the source, and write a separate output file.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
