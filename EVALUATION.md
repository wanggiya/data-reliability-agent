# Evaluation plan

## Primary metric

Finding-level F1 across controlled benchmark cases. A finding is keyed by dataset and finding type.

## Fair comparison

The baseline and agent receive exactly the same CSV files. The baseline runs missing-value and exact-duplicate checks. The agent can select from the documented deterministic catalog. Both are scored against `benchmark/expected_findings.json`.

## Cases

The current suite includes 11 cases: clean data, missing values, exact duplicates, duplicate identifiers, inconsistent categories, a missing month, negative measures, extreme outliers, a suspicious zero column, a cross-field total mismatch, and combined problems.

## Run

```bash
make evaluate
```

Report precision, recall, and F1 for both solutions. Keep all failures in the results rather than removing difficult cases.

Current deterministic benchmark result:

| Solution | Precision | Recall | F1 |
|---|---:|---:|---:|
| Baseline | 1.000 | 0.200 | 0.333 |
| Agent workflow | 1.000 | 1.000 | 1.000 |

These are controlled synthetic cases, not a claim of perfect real-world accuracy. The value of the benchmark is transparent regression detection and a fair baseline comparison.
