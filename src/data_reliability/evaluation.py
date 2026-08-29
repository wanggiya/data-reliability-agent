from __future__ import annotations

import json
from pathlib import Path

from .baseline import run_baseline
from .orchestrator import investigate


def score(expected: set[str], observed: set[str]) -> dict[str, float | int]:
    tp = len(expected & observed)
    fp = len(observed - expected)
    fn = len(expected - observed)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def evaluate(manifest_path: str | Path, mode: str = "deterministic") -> dict[str, dict[str, float | int]]:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    root = Path(manifest_path).parent
    expected_all: set[str] = set()
    baseline_all: set[str] = set()
    agent_all: set[str] = set()
    for case in manifest["cases"]:
        expected_all |= {f"{case['file']}::{finding}" for finding in case["expected"]}
        baseline = run_baseline(root / "cases" / case["file"])
        baseline_all |= {f"{case['file']}::{finding.finding_type}" for finding in baseline}
        result = investigate(root / "cases" / case["file"], "Find supported data reliability problems", mode=mode)
        agent_all |= {f"{case['file']}::{finding.finding_type}" for finding in result.findings}
    return {"baseline": score(expected_all, baseline_all), "agent": score(expected_all, agent_all)}

