# Data Reliability Investigation

- Run: `06cafb203d93`
- Dataset: `benchmark/cases/case_06_multi_issue.csv`
- Shape: 8 rows × 6 columns
- Planning source: `deterministic`
- Goal: Assess whether this monthly operations dataset is safe for KPI reporting

## Investigation plan

- `missing_values` — Selected from dataset schema and the user's reliability goal.
- `duplicate_rows` — Selected from dataset schema and the user's reliability goal.
- `negative_values` — Selected from dataset schema and the user's reliability goal.
- `suspicious_zeros` — Selected from dataset schema and the user's reliability goal.
- `numeric_outliers` — Selected from dataset schema and the user's reliability goal.
- `category_inconsistency` — Selected from dataset schema and the user's reliability goal.
- `duplicate_ids` — Selected from dataset schema and the user's reliability goal.
- `date_gaps` — Selected from dataset schema and the user's reliability goal.

## Verified findings

### 1. Negative Values (critical)

1 negative values in non-negative measure revenue

Evidence: check=`negative_values`, column=`revenue`, count=1, rows=[1], values=[-5]

### 2. Suspicious Zeros (warning)

8/8 values in unused_metric are zero

Evidence: check=`suspicious_zeros`, column=`unused_metric`, count=8, rows=[], values=[]

### 3. Numeric Outliers (warning)

1 extreme IQR outliers in cases

Evidence: check=`numeric_outliers`, column=`cases`, count=1, rows=[6], values=[5000]

### 4. Category Inconsistency (warning)

Formatting variants represent the same normalized category in region

Evidence: check=`category_inconsistency`, column=`region`, count=2, rows=[], values=[['WEST ', 'West']]

## Verification

- Accepted findings: 4
- Rejected unsupported findings: 0

## Proposed repairs — approval required

- `null-negative-revenue`: replace_negative_with_null; affected≈1; risk=high: a negative value may be a valid correction or refund
- `normalize-category-region`: normalize_category_formatting; affected≈2; risk=medium: trims whitespace and unifies case variants using the most frequent spelling

## Safety note

Investigation is read-only. Repairs require explicit proposal IDs, never overwrite the source, and write a separate output file.
