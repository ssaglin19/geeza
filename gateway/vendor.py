"""Fake vendor site as a scripted Driver, so the real flow engine runs the bill-pay flow."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
from boosh_flow import Driver, load_flow, run_flow  # noqa: E402

HOST = "https://demo.lakeshore-power.test"
FLOW_PATH = ROOT / "flows" / "examples" / "demo-utility-pay.json"


class VendorDriver(Driver):
    def __init__(self, amount: str):
        self.amount, self.page, self.paid = amount, "login", False

    def goto(self, url): self.page = "login"

    def snapshot(self):
        if self.page == "login":
            return {"url": HOST + "/login", "elements": [{"selector": "#username"}, {"selector": "#password"}, {"text": "Sign in"}]}
        if self.page == "account":
            return {"url": HOST + "/account/overview", "elements": [
                {"selector": ".amount-due", "text": "Amount due", "value": self.amount}, {"text": "Pay Now"}]}
        return {"url": HOST + "/pay/review", "elements": [
            {"text": "Confirm payment"}, {"text": "Lakeshore Power"}, {"selector": "button.pay-submit"}]}

    def fill(self, selector, value): pass

    def click(self, selector=None, text=None):
        if text == "Sign in": self.page = "account"
        elif text == "Pay Now": self.page = "review"
        elif selector == "button.pay-submit": self.paid = True

    def read_text(self, selector): return self.amount


def run_demo_flow(amount: str, last_bill: float, approver):
    """Run the real engine against the fake vendor. approver(question)->bool is the approval gate."""
    flow = load_flow(FLOW_PATH)
    driver = VendorDriver(amount)
    ctx = {"credentials": {"lakeshore": {"username": "demo-user", "password": "demo-pass"}},
           "history": {"lakeshore_last_amount": last_bill}}
    events = run_flow(flow, driver, ctx, approver=approver)
    return events, driver.paid
