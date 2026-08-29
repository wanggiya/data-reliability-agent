# Evaluation plan

## Primary metric

Finding-level F1 across controlled benchmark cases. A finding is keyed by dataset and finding type.

## Fair comparison

The baseline and agent receive exactly the same CSV files. The baseline runs missing-value and exact-duplicate checks. The agent can select from the documented deterministic catalog. Both are scored against `benchmark/expected_findings.json`.

## Cases

Day 1 includes six cases: clean data, missing value, duplicates, inconsistent category formatting, missing month, and a multi-problem file. Day 2 should expand this to at least ten cases and add one deliberately difficult cross-field inconsistency.

## Run

```bash
make evaluate
```

Report precision, recall, and F1 for both solutions. Keep all failures in the results rather than removing difficult cases.

