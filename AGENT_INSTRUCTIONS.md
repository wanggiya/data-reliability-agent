# Agent instructions and contracts

## Investigator

Purpose: select useful checks based on the user's decision goal and a schema-only profile.

Constraints:

- Return JSON only.
- Select only names from the allowlisted `CheckName` catalog.
- Do not claim that a problem exists; planning is not evidence.
- Do not request credentials, private data, network access, or arbitrary code execution.
- An empty or invalid response triggers the deterministic planner.

The exact runtime prompt is versioned in `src/data_reliability/investigator.py`.

## Executor

Purpose: run the selected deterministic checks.

Constraints:

- Read the source table without modifying it.
- Return structured `Evidence` records.
- Include calculated count and, when appropriate, bounded row/value samples.
- Never execute model-generated Python, SQL, shell, or expressions.

## Verifier

Purpose: prevent unsupported claims from entering the final report.

Constraints:

- Reject duplicate evidence.
- Reject non-positive evidence counts.
- Reject inconsistent row-count evidence.
- Build findings only from accepted evidence; do not invent narrative facts.

## Repair planner and executor

Purpose: translate selected finding types into bounded repair proposals.

Constraints:

- Proposal is not approval.
- Only allowlisted actions can run.
- The human must provide exact proposal IDs.
- Unknown IDs fail closed.
- Source overwrite is forbidden.
- A new output file is mandatory.

