import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fixtures
from boosh_flow import load_flow, run_flow


def kinds(events):
    return [e["event"] for e in events]


class TestHappyPath(unittest.TestCase):
    def test_full_flow_completes(self):
        flow = load_flow(fixtures.example_flow_path())
        driver = fixtures.FixtureDriver([fixtures.LOGIN, fixtures.DASHBOARD, fixtures.REVIEW])
        events = run_flow(flow, driver, fixtures.make_ctx(), approver=lambda q: True)

        self.assertEqual(
            kinds(events),
            [
                "PAGE_MATCHED", "PAGE_MATCHED", "READ", "GATE_PASSED",
                "PAGE_MATCHED", "APPROVAL_REQUIRED", "APPROVAL_RESULT", "FLOW_COMPLETE",
            ],
        )
        # credentials resolved from ctx, not stored in the flow file
        self.assertEqual(driver.filled["#username"], "mom@example.com")
        self.assertEqual(driver.filled["#password"], "hunter2")
        # amount read from the page and gated
        read = next(e for e in events if e["event"] == "READ")
        self.assertEqual(read["value"], "86.90")

    def test_page_confidences_logged(self):
        flow = load_flow(fixtures.example_flow_path())
        driver = fixtures.FixtureDriver([fixtures.LOGIN, fixtures.DASHBOARD, fixtures.REVIEW])
        events = run_flow(flow, driver, fixtures.make_ctx(), approver=lambda q: True)
        for ev in events:
            if ev["event"] == "PAGE_MATCHED":
                self.assertEqual(ev["band"], "act")
                self.assertGreaterEqual(ev["confidence"], 0.85)


class TestFailClosed(unittest.TestCase):
    def test_gate_failure_aborts_before_approval(self):
        flow = load_flow(fixtures.example_flow_path())
        driver = fixtures.FixtureDriver([fixtures.LOGIN, fixtures.DASHBOARD, fixtures.REVIEW])
        ctx = fixtures.make_ctx(last_amount=50.00)  # 86.90 is 74% above baseline
        events = run_flow(flow, driver, ctx, approver=lambda q: True)

        self.assertIn("GATE_FAILED", kinds(events))
        self.assertIn("FLOW_ABORTED", kinds(events))
        self.assertNotIn("APPROVAL_REQUIRED", kinds(events))  # sanity gate runs first
        aborted = next(e for e in events if e["event"] == "FLOW_ABORTED")
        self.assertEqual(aborted["reason"], "gate_failed")

    def test_approval_denial_aborts(self):
        flow = load_flow(fixtures.example_flow_path())
        driver = fixtures.FixtureDriver([fixtures.LOGIN, fixtures.DASHBOARD, fixtures.REVIEW])
        events = run_flow(flow, driver, fixtures.make_ctx(), approver=lambda q: False)
        self.assertIn("APPROVAL_REQUIRED", kinds(events))
        aborted = next(e for e in events if e["event"] == "FLOW_ABORTED")
        self.assertEqual(aborted["reason"], "approval_denied")

    def test_no_approver_fails_closed(self):
        flow = load_flow(fixtures.example_flow_path())
        driver = fixtures.FixtureDriver([fixtures.LOGIN, fixtures.DASHBOARD, fixtures.REVIEW])
        events = run_flow(flow, driver, fixtures.make_ctx())  # approver=None
        self.assertIn("APPROVAL_REQUIRED", kinds(events))
        aborted = next(e for e in events if e["event"] == "FLOW_ABORTED")
        self.assertEqual(aborted["reason"], "approval_denied")


class TestPageEdgeCases(unittest.TestCase):
    def test_unrecognized_page_aborts(self):
        flow = load_flow(fixtures.example_flow_path())
        blank = {"url": "about:blank", "elements": []}
        driver = fixtures.FixtureDriver([blank])
        events = run_flow(flow, driver, fixtures.make_ctx(), approver=lambda q: True)
        self.assertIn("PAGE_UNRECOGNIZED", kinds(events))
        aborted = next(e for e in events if e["event"] == "FLOW_ABORTED")
        self.assertEqual(aborted["reason"], "page_unrecognized")

    def test_confirm_band_page_requires_human(self):
        flow = load_flow(fixtures.example_flow_path())
        shaky_login = {
            "url": "https://www.consumersenergy.com/login",
            "elements": [{"selector": "#username"}, {"text": "Sign in"}],  # 2/3 anchors
        }
        driver = fixtures.FixtureDriver([shaky_login, fixtures.DASHBOARD, fixtures.REVIEW])
        events = run_flow(flow, driver, fixtures.make_ctx(), approver=lambda q: True)
        self.assertIn("PAGE_CONFIRM_REQUIRED", kinds(events))
        self.assertIn("FLOW_COMPLETE", kinds(events))

    def test_low_confidence_page_aborts(self):
        flow = load_flow(fixtures.example_flow_path())
        wrong_page = {
            "url": "https://www.consumersenergy.com/login",
            "elements": [{"selector": "#username"}],  # 1/3 anchors = 0.33
        }
        driver = fixtures.FixtureDriver([wrong_page])
        events = run_flow(flow, driver, fixtures.make_ctx(), approver=lambda q: True)
        aborted = next(e for e in events if e["event"] == "FLOW_ABORTED")
        self.assertEqual(aborted["reason"], "low_page_confidence")

    def test_phishing_lookalike_never_matches(self):
        # Same DOM, attacker domain: url gate must zero it out.
        flow = load_flow(fixtures.example_flow_path())
        evil = {"url": "https://consumers-energy-billing.com/login",
                "elements": fixtures.LOGIN["elements"]}
        driver = fixtures.FixtureDriver([evil])
        events = run_flow(flow, driver, fixtures.make_ctx(), approver=lambda q: True)
        aborted = next(e for e in events if e["event"] == "FLOW_ABORTED")
        self.assertEqual(aborted["reason"], "page_unrecognized")


if __name__ == "__main__":
    unittest.main()
