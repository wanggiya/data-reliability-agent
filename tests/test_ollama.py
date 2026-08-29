from __future__ import annotations

import unittest

from data_reliability.investigator import ollama_plan
from data_reliability.models import DatasetProfile


class OllamaFallbackTests(unittest.TestCase):
    def test_unreachable_ollama_falls_back(self) -> None:
        profile = DatasetProfile(path="x.csv", rows=2, columns=1, column_names=["id"], dtypes={"id": "int64"}, null_counts={"id": 0}, sample=[], numeric_columns=["id"], date_candidates=[], id_candidates=["id"])
        plan = ollama_plan(profile, "test", base_url="http://127.0.0.1:1")
        self.assertTrue(plan.source.startswith("deterministic-fallback"))
        self.assertGreater(len(plan.checks), 0)


if __name__ == "__main__":
    unittest.main()

