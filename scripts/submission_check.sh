#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[1/5] Python syntax"
PYTHONPATH=src python3 -m compileall -q src tests

echo "[2/5] Browser JavaScript syntax"
node --input-type=module --check < web/app.js

echo "[3/5] Unit and contract tests"
PYTHONPATH=src python3 -m unittest discover -s tests -v

echo "[4/5] Baseline-versus-advanced benchmark"
PYTHONPATH=src python3 benchmark/generate_cases.py
PYTHONPATH=src python3 -m data_reliability.cli evaluate benchmark/expected_findings.json

echo "[5/5] Submission files"
for required in README.md IMPROVEMENT_CHANGELOG.md EVALUATION.md THIRD_PARTY_NOTICES.md docs/REPRODUCTION.md docs/DEMO_SCRIPT.md AGENT_INSTRUCTIONS.md trajectories/README.md; do
  test -s "$required" || { echo "Missing required file: $required" >&2; exit 1; }
done

echo "Submission check passed. Review git status and the manual checklist before tagging."
