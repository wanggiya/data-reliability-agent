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
        "## Safety note",
        "",
        "This run was read-only. Proposed repairs require explicit human approval and are not part of the Day 1 implementation.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path

