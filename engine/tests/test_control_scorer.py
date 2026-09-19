"""Tests for control scoring."""
import unittest

from boosh_flow.control_scorer import (
    Control, TfidfControlScorer, extract_controls, best_control,
)


class TestExtractControls(unittest.TestCase):
    def test_extracts_buttons_links_inputs(self):
        snapshot = {
            "elements": [
                {"tag": "button", "text": "Pay Now", "selector": "#pay"},
                {"tag": "a", "text": "View Bill", "href": "/bill", "selector": "a.bill"},
                {"tag": "input", "type": "submit", "text": "Submit", "selector": "#submit"},
                {"tag": "div", "text": "Not a control"},  # ignored
            ]
        }
        controls = extract_controls(snapshot)
        self.assertEqual(len(controls), 3)
        self.assertEqual(controls[0].tag, "button")
        self.assertEqual(controls[1].tag, "a")
        self.assertEqual(controls[2].tag, "input")


class TestTfidfScorer(unittest.TestCase):
    def setUp(self):
        self.scorer = TfidfControlScorer()

    def test_pay_button_scores_high_for_pay_bill(self):
        controls = [
            Control("button", "Pay Now", "", "", "", "#pay"),
            Control("a", "Contact Us", "", "/contact", "", "#contact"),
        ]
        scores = self.scorer.score(controls, "pay bill")
        self.assertEqual(scores[0].control.text, "Pay Now")
        self.assertGreater(scores[0].score, 0.3)  # 1/3 terms * 1.2 button boost = 0.4

    def test_login_button_scores_high_for_log_in(self):
        controls = [
            Control("button", "Sign In", "", "", "", "#login"),
            Control("button", "Pay Bill", "", "", "", "#pay"),
        ]
        scores = self.scorer.score(controls, "log in")
        self.assertEqual(scores[0].control.text, "Sign In")

    def test_no_match_returns_low_score(self):
        controls = [
            Control("button", "Click Here", "", "", "", "#click"),
        ]
        scores = self.scorer.score(controls, "pay bill")
        self.assertLess(scores[0].score, 0.3)


class TestBestControl(unittest.TestCase):
    def test_finds_pay_button(self):
        snapshot = {
            "elements": [
                {"tag": "button", "text": "Pay Now", "selector": "#pay"},
                {"tag": "a", "text": "Home", "href": "/", "selector": "#home"},
            ]
        }
        result = best_control(snapshot, "pay bill")
        self.assertIsNotNone(result)
        self.assertEqual(result.control.selector, "#pay")

    def test_returns_none_when_no_good_match(self):
        snapshot = {
            "elements": [
                {"tag": "button", "text": "Click Here", "selector": "#click"},
            ]
        }
        result = best_control(snapshot, "pay bill")
        self.assertIsNone(result)

    def test_returns_none_when_no_controls(self):
        snapshot = {"elements": []}
        result = best_control(snapshot, "pay bill")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
