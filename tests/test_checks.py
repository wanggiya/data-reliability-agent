from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from data_reliability.baseline import run_baseline
from data_reliability.checks import execute_plan
from data_reliability.investigator import deterministic_plan
from data_reliability.profiler import profile_dataset
from data_reliability.verifier import verify_evidence


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "sample.csv"
        pd.DataFrame({
            "record_id": [1, 2, 2, 4, 5, 6],
            "month": ["2026-01-01", "2026-02-01", "2026-02-01", "2026-04-01", "2026-05-01", "2026-06-01"],
            "region": ["North", "South", "South", " east ", "EAST", "West"],
            "cases": [10, 11, 11, -1, 12, 999],
        }).to_csv(self.path, index=False)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_profile_and_plan(self) -> None:
        _, profile = profile_dataset(self.path)
        plan = deterministic_plan(profile, "validate")
        self.assertIn("record_id", profile.id_candidates)
        self.assertIn("month", profile.date_candidates)
        self.assertIn("duplicate_ids", [c.value for c in plan.checks])

    def test_evidence_is_verified(self) -> None:
        frame, profile = profile_dataset(self.path)
        plan = deterministic_plan(profile, "validate")
        evidence = execute_plan(plan.checks, frame, profile)
        findings, summary = verify_evidence(evidence)
        types = {f.finding_type for f in findings}
        self.assertIn("duplicate_ids", types)
        self.assertIn("date_gaps", types)
        self.assertIn("negative_values", types)
        self.assertEqual(summary.accepted, len(findings))

    def test_baseline_is_intentionally_limited(self) -> None:
        types = {e.finding_type for e in run_baseline(self.path)}
        self.assertIn("duplicate_rows", types)
        self.assertNotIn("date_gaps", types)


if __name__ == "__main__":
    unittest.main()

