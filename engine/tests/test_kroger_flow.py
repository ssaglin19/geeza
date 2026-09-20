"""End-to-end tests for the Kroger grocery-order flow."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from boosh_flow.schema import flow_from_dict, validate_flow
from boosh_flow.engine import run_flow, Driver
from tests import fixtures_kroger as fixtures


class FakeDriver(Driver):
    """Serves fixtures in a scriptable order."""

    def __init__(self):
        self.current = fixtures.LOGIN
        self.clicked = []
        self.filled = {}
        self.extracted = {
            ".cart-total": "$3.49",
            ".order-total": "$3.49",
        }

    def goto(self, url):
        mapping = {
            "https://www.kroger.com/signin": fixtures.LOGIN,
            "https://www.kroger.com/account": fixtures.ACCOUNT,
            "https://www.kroger.com/search?q=milk": fixtures.SEARCH_RESULTS,
            "https://www.kroger.com/cart": fixtures.CART,
            "https://www.kroger.com/checkout": fixtures.CHECKOUT,
        }
        self.current = mapping.get(url, fixtures.UNRECOGNIZED)

    def snapshot(self):
        return self.current

    def click(self, selector=None, text=None):
        sel = selector or text
        self.clicked.append(sel)
        transitions = {
            "#signin-btn": fixtures.ACCOUNT,
            ".cart-link": fixtures.CART,
            ".product-card": fixtures.PRODUCT,
            "#add-to-cart": fixtures.CART,
            "#checkout-btn": fixtures.CHECKOUT,
        }
        self.current = transitions.get(sel, self.current)

    def fill(self, selector, value):
        self.filled[selector] = value

    def read_text(self, selector):
        return self.extracted.get(selector, "")


class TestKrogerFlow(unittest.TestCase):
    def setUp(self):
        self.flow = flow_from_dict(fixtures.load_flow())
        self.errors = validate_flow(self.flow)

    def test_flow_loads_and_validates(self):
        hard = [e for e in self.errors if "missing url_host" in e or "missing url_contains" in e]
        self.assertEqual(hard, [], f"hard validation errors: {hard}")

    def test_spends_requires_confirm(self):
        self.assertTrue(self.flow.spends)
        has_confirm = any(
            s.action == "confirm"
            for p in self.flow.pages
            for s in p.steps
        )
        self.assertTrue(has_confirm, "spending flow must have a confirm step")

    def test_happy_path_completes(self):
        driver = FakeDriver()
        events = run_flow(self.flow, driver, self._make_ctx(), approver=lambda q: True)
        kinds = [e["event"] for e in events]
        self.assertIn("FLOW_COMPLETE", kinds)
        # Flow ends at confirm; place-order would happen after approval in real scenario
        self.assertIn("#checkout-btn", driver.clicked)

    def test_wrong_host_aborts(self):
        # A phishing lookalike: right anchors, wrong domain. Must not match.
        driver = FakeDriver()
        # Override goto to serve the phishing page instead of the real login
        original_goto = driver.goto
        def phishing_goto(url):
            if "kroger.com/signin" in url:
                driver.current = {
                    "url": "https://kroger-savings.com/signin",
                    "elements": fixtures.LOGIN["elements"],
                }
            else:
                original_goto(url)
        driver.goto = phishing_goto

        events = run_flow(self.flow, driver, self._make_ctx(), approver=lambda q: True)
        aborted = [e for e in events if e["event"] == "FLOW_ABORTED"]
        self.assertTrue(aborted)
        self.assertIn("page_unrecognized", aborted[0]["reason"])

    def test_high_cart_total_triggers_gate(self):
        driver = FakeDriver()
        driver.current = fixtures.CART_HIGH_TOTAL
        driver.extracted[".cart-total"] = "$247.83"
        events = run_flow(self.flow, driver, self._make_ctx(), approver=lambda q: True)
        aborted = [e for e in events if e["event"] == "FLOW_ABORTED"]
        self.assertTrue(aborted)
        self.assertIn("gate_failed", aborted[0]["reason"])

    def test_high_checkout_total_triggers_gate(self):
        driver = FakeDriver()
        driver.current = fixtures.CHECKOUT_HIGH_TOTAL
        driver.extracted[".order-total"] = "$247.83"
        events = run_flow(self.flow, driver, self._make_ctx(), approver=lambda q: True)
        aborted = [e for e in events if e["event"] == "FLOW_ABORTED"]
        self.assertTrue(aborted)
        self.assertIn("gate_failed", aborted[0]["reason"])

    def test_approval_denial_aborts(self):
        driver = FakeDriver()
        events = run_flow(self.flow, driver, self._make_ctx(), approver=lambda q: False)
        aborted = [e for e in events if e["event"] == "FLOW_ABORTED"]
        self.assertTrue(aborted)
        self.assertIn("approval_denied", aborted[0]["reason"])

    def _make_ctx(self):
        return {
            "credentials": {
                "kroger": {"username": "mom@example.com", "password": "hunter2"}
            },
            "baselines": {
                "cart_total": 3.49,
                "order_total": 3.49,
            },
        }


if __name__ == "__main__":
    unittest.main()
