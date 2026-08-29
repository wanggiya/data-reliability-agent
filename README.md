# Data Reliability Investigation Agent

An evidence-first workflow for analysts who receive unfamiliar CSV files and need to decide whether they are reliable enough for analysis or KPI reporting.

## User and bottleneck

Data analysts regularly inherit files without trustworthy documentation. Manual inspection is inconsistent and a direct LLM prompt can make plausible claims without calculating evidence. This project combines agent-selected investigation plans with deterministic checks and independent verification. Every accepted claim points to calculated evidence.

## Day 1 capability

- Profiles CSV structure without modifying the source.
- Uses Ollama to select checks from a controlled tool catalog.
- Falls back deterministically when Ollama is unavailable.
- Detects missing values, duplicates, duplicate IDs, negative measures, suspicious zeros, extreme outliers, category formatting collisions, monthly gaps, and selected total mismatches.
- Independently verifies evidence contracts.
- Writes a Markdown report, structured JSON result, and JSONL trajectory.
- Includes a fair basic baseline and generated benchmark cases.

## Quick start on WSL Ubuntu

```bash
cd ~/data-reliability-agent
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
make test
make demo
```

Run with Ollama:

```bash
ollama list
export OLLAMA_MODEL=qwen2.5-coder:7b  # replace with an installed model
curl http://localhost:11434/api/tags
make benchmark
data-reliability investigate benchmark/cases/case_06_multi_issue.csv \
  --goal "Assess whether this dataset is safe for monthly KPI reporting" \
  --mode ollama
```

If Ollama runs on Windows and WSL cannot reach `localhost`, determine the Windows host address and set:

```bash
export OLLAMA_BASE_URL=http://WINDOWS_HOST_IP:11434
```

Do not hard-code that address in the repository.

## Exact commands

```bash
make benchmark
make baseline
make demo
make evaluate
```

The demo writes:

```text
outputs/<run-id>/report.md
outputs/<run-id>/result.json
outputs/<run-id>/trajectory.jsonl
```

## Baseline

The baseline is an ordinary profiling script that detects only missing cells and exact duplicate rows. The final workflow receives the same files but can select a broader set of deterministic checks and verifies every resulting claim.

## Safety

Day 1 is read-only. It does not run arbitrary generated code or modify uploaded datasets. Repairs are intentionally deferred until a human-approval boundary is implemented.

## Current limitations

- CSV only on Day 1.
- Semantic domain rules are limited without an explicit data contract.
- IQR outliers are investigation leads, not proof of erroneous data.
- Ollama chooses checks but does not directly author evidence or final factual claims.

