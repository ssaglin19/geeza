import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from boosh_flow import amount_sanity, evaluate_gate


class TestAmountSanity(unittest.TestCase):
    def test_within_tolerance_passes(self):
        ok, detail = amount_sanity("86.90", 84.00, 15)
        self.assertTrue(ok)

    def test_deviation_fails(self):
        ok, detail = amount_sanity("$200", "$84", 15)
        self.assertFalse(ok)
        self.assertIn("deviates", detail)

    def test_garbage_fails_closed(self):
        ok, _ = amount_sanity("N/A", "84.00", 15)
        self.assertFalse(ok)

    def test_missing_baseline_fails(self):
        ok, _ = amount_sanity("86.90", None, 15)
        self.assertFalse(ok)

    def test_dollar_and_comma_formats_parse(self):
        ok, _ = amount_sanity("$1,286.40", "1284.00", 15)
        self.assertTrue(ok)


class TestEvaluateGate(unittest.TestCase):
    def test_gate_reads_context_paths(self):
        ctx = {"history": {"utility_last": 84.0}, "amount_due": "86.90"}
        params = {"type": "amount_sanity", "value_key": "amount_due",
                  "last_key": "history.utility_last", "within_pct": 15}
        ok, _ = evaluate_gate(params, ctx)
        self.assertTrue(ok)

    def test_unknown_type_fails(self):
        ok, _ = evaluate_gate({"type": "vibes"}, {})
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
