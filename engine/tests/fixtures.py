"""Scripted pages and driver for engine tests.

Mirrors flows/examples/consumers-energy-pay.json so the example flow is what
the tests actually execute.
"""
from __future__ import annotations

from pathlib import Path

from boosh_flow import Driver

LOGIN = {
    "url": "https://www.consumersenergy.com/login",
    "elements": [
        {"selector": "#username"},
        {"selector": "#password"},
        {"text": "Sign in"},
    ],
}

DASHBOARD = {
    "url": "https://www.consumersenergy.com/account/overview",
    "elements": [
        {"selector": ".amount-due", "text": "Amount due", "value": "86.90"},
        {"text": "Pay Now"},
    ],
}

REVIEW = {
    "url": "https://www.consumersenergy.com/pay/review",
    "elements": [
        {"text": "Confirm payment"},
        {"text": "Consumers Energy"},
        {"selector": "button.pay-submit"},
    ],
}


class FixtureDriver(Driver):
    """Clicks advance the scripted page list; fills and reads are recorded."""

    def __init__(self, pages):
        self.pages = list(pages)
        self.i = 0
        self.filled = {}
        self.clicks = []

    def goto(self, url: str) -> None:
        self.i = 0

    def snapshot(self) -> dict:
        return self.pages[min(self.i, len(self.pages) - 1)]

    def fill(self, selector: str, value: str) -> None:
        self.filled[selector] = value

    def click(self, selector=None, text=None) -> None:
        self.clicks.append(selector or text)
        self.i += 1

    def read_text(self, selector: str) -> str:
        for el in self.snapshot().get("elements", []):
            if el.get("selector") == selector:
                return el.get("value") or el.get("text") or ""
        return ""


def make_ctx(last_amount=84.00) -> dict:
    return {
        "credentials": {
            "consumers_energy": {"username": "mom@example.com", "password": "hunter2"}
        },
        "history": {"consumers_energy_last_amount": last_amount},
    }


def example_flow_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    return root / "flows" / "examples" / "consumers-energy-pay.json"
