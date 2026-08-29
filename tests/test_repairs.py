from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from data_reliability.models import CheckName, Evidence, Finding, Severity
from data_reliability.profiler import load_table, write_table
from data_reliability.repairs import apply_approved_repairs, proposals_from_findings


def finding(kind: str, column: str | None, count: int) -> Finding:
    evidence = Evidence(check=CheckName.category_inconsistency if kind == "category_inconsistency" else CheckName.negative_values, finding_type=kind, column=column, count=count, detail=f"test {kind}")
    return Finding(finding_type=kind, severity=Severity.warning, title=kind, detail=evidence.detail, evidence=evidence, verified=True)


class RepairTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.source = Path(self.temp.name) / "source.csv"
        pd.DataFrame({"region": [" North ", "South"], "cases": [-1, 2]}).to_csv(self.source, index=False)
        self.proposals = proposals_from_findings([
            finding("category_inconsistency", "region", 1),
            finding("negative_values", "cases", 1),
        ])

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_requires_explicit_approval(self) -> None:
        with self.assertRaises(ValueError):
            apply_approved_repairs(self.source, Path(self.temp.name) / "out.csv", self.proposals, set())

    def test_forbids_source_overwrite(self) -> None:
        with self.assertRaises(ValueError):
            apply_approved_repairs(self.source, self.source, self.proposals, {"normalize-category-region"})

    def test_applies_only_approved_proposal(self) -> None:
        output = Path(self.temp.name) / "repaired.csv"
        result = apply_approved_repairs(self.source, output, self.proposals, {"normalize-category-region"})
        repaired = pd.read_csv(output)
        self.assertEqual(repaired.loc[0, "region"], "North")
        self.assertEqual(repaired.loc[0, "cases"], -1)
        self.assertEqual(len(result.changes_applied), 1)

    def test_json_round_trip(self) -> None:
        source = Path(self.temp.name) / "source.json"
        output = Path(self.temp.name) / "output.json"
        frame = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        write_table(frame, source)
        loaded = load_table(source)
        write_table(loaded, output)
        self.assertEqual(load_table(output).to_dict(orient="records"), frame.to_dict(orient="records"))


if __name__ == "__main__":
    unittest.main()
