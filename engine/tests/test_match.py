import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fixtures
from boosh_flow import load_flow, page_confidence, band, ABORT, ACT, CONFIRM


class TestMatch(unittest.TestCase):
    def setUp(self):
        self.flow = load_flow(fixtures.example_flow_path())
        self.login = next(p for p in self.flow.pages if p.name == "login")

    def test_wrong_host_is_hard_zero(self):
        # Phishing lookalike: right anchors, right path, wrong domain.
        snap = {"url": "https://consumers-energy-billing.com/login", "elements": fixtures.LOGIN["elements"]}
        result = page_confidence(snap, self.login)
        self.assertEqual(result.confidence, 0.0)
        self.assertIn("host", result.failed)

    def test_wrong_path_is_hard_zero(self):
        snap = {"url": "https://www.consumersenergy.com/billing", "elements": fixtures.LOGIN["elements"]}
        result = page_confidence(snap, self.login)
        self.assertEqual(result.confidence, 0.0)
        self.assertIn("path", result.failed)

    def test_full_anchor_hit(self):
        result = page_confidence(fixtures.LOGIN, self.login)
        self.assertEqual(result.confidence, 1.0)
        self.assertEqual(result.failed, [])

    def test_partial_anchor_hit_lands_in_confirm_band(self):
        snap = {
            "url": "https://www.consumersenergy.com/login",
            "elements": [
                {"selector": "#username"},
                {"text": "Sign in"},
            ],
        }
        result = page_confidence(snap, self.login)
        self.assertAlmostEqual(result.confidence, 2 / 3, places=3)
        self.assertEqual(band(result.confidence, self.flow.thresholds), CONFIRM)


class TestBands(unittest.TestCase):
    def test_band_edges(self):
        self.assertEqual(band(0.85), ACT)
        self.assertEqual(band(0.8499), CONFIRM)
        self.assertEqual(band(0.5), CONFIRM)
        self.assertEqual(band(0.4999), ABORT)
        self.assertEqual(band(0.0), ABORT)


if __name__ == "__main__":
    unittest.main()
