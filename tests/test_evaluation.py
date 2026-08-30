from __future__ import annotations

import unittest

from data_reliability.evaluation import score


class EvaluationTests(unittest.TestCase):
    def test_score(self) -> None:
        metrics = score({"a", "b", "c"}, {"a", "b", "x"})
        self.assertEqual(metrics["tp"], 2)
        self.assertEqual(metrics["fp"], 1)
        self.assertEqual(metrics["fn"], 1)
        self.assertAlmostEqual(metrics["f1"], 2 / 3)


if __name__ == "__main__":
    unittest.main()
