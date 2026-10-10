import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT))
from boosh_flow import bill_explainer as be
from boosh_flow.nebius import MockClient
from gateway import demo_data
from gateway.assistant import Assistant

H = demo_data.BILL_HISTORY


class Live:
    live = True
    used_fallback = False
    last_model = "stub"
    def __init__(self, text): self.text = text
    def complete(self, messages, **kw): return self.text


class TestMath(unittest.TestCase):
    def test_fixture_totals_match_demo_amounts(self):
        self.assertEqual(be.total(demo_data.BILL_CURRENT["normal"]), float(demo_data.SCENARIOS["normal"]))
        self.assertEqual(be.total(demo_data.BILL_CURRENT["suspicious"]), float(demo_data.SCENARIOS["suspicious"]))
        self.assertEqual(be.total(H[-1]), demo_data.LAST_BILL)

    def test_effects_add_up_to_change(self):
        for k in ("normal", "suspicious"):
            a = be.analyze(H, demo_data.BILL_CURRENT[k])
            self.assertAlmostEqual(sum(a["effects"].values()), a["change"], delta=0.03)

    def test_normal_is_not_a_spike(self):
        a = be.analyze(H, demo_data.BILL_CURRENT["normal"])
        self.assertFalse(a["spike"])
        self.assertEqual(be.next_steps(a), [])
        self.assertIn("Nothing looks unusual", be.template(a))

    def test_spike_names_the_extra_charge(self):
        a = be.analyze(H, demo_data.BILL_CURRENT["suspicious"])
        self.assertTrue(a["spike"])
        self.assertEqual(a["main_reason"], "extra charges")
        self.assertIn("Prior-period estimate adjustment", be.template(a))
        self.assertIn("$228.50", be.template(a))
        self.assertEqual(len(be.next_steps(a)), 3)

    def test_rate_increase_is_attributed_to_rate(self):
        cur = {"period": "Feb", "days": 28, "kwh": 510, "rate": 0.19, "fixed": 12.38, "extras": []}
        a = be.analyze(H, cur)
        self.assertEqual(a["main_reason"], "rate")

    def test_needs_history(self):
        with self.assertRaises(ValueError):
            be.analyze([], demo_data.BILL_CURRENT["normal"])

    def test_draft_has_no_savings_claim_or_entitlement(self):
        a = be.analyze(H, demo_data.BILL_CURRENT["suspicious"])
        d = be.draft_review_request(a).lower()
        self.assertNotIn("entitled", d)
        self.assertNotIn("save", d)
        self.assertIn("$412.00", be.draft_review_request(a))


class TestModelWording(unittest.TestCase):
    def setUp(self):
        self.a = be.analyze(H, demo_data.BILL_CURRENT["suspicious"])

    def test_good_model_text_is_used(self):
        t = "Your January bill is $412.00, which is $329.18 more than usual. A $228.50 estimate adjustment is the biggest part."
        out = be.explain(self.a, Live(t))
        self.assertEqual(out["source"], "model")

    def test_invented_number_is_rejected(self):
        out = be.explain(self.a, Live("Your bill is $412.00 and you will save $120 if you switch."))
        self.assertEqual(out["source"], "code")
        self.assertIn("$412.00", out["text"])

    def test_json_or_empty_is_rejected(self):
        for bad in ("", '{"reply": "x"}'):
            self.assertEqual(be.explain(self.a, Live(bad))["source"], "code")

    def test_offline_client_uses_code(self):
        self.assertEqual(be.explain(self.a, MockClient())["source"], "code")


class TestAssistant(unittest.TestCase):
    def ask(self, scenario, text):
        return Assistant(MockClient(), scenario).handle(text, "t")

    def test_spike_question(self):
        r = self.ask("suspicious", "Why is my electric bill so high?")
        self.assertEqual(r["tool"], "explain_bill")
        self.assertIn("$412.00", r["response"])
        self.assertIn("Draft billing review request (not sent)", r["response"])
        self.assertIn("heat, cooling or medical equipment", r["response"])
        self.assertEqual(r["actions"][0]["type"], "bill_explained")

    def test_normal_bill_has_no_draft(self):
        r = self.ask("normal", "why did my electric bill go up")
        self.assertEqual(r["tool"], "explain_bill")
        self.assertNotIn("Draft billing review", r["response"])

    def test_nothing_is_pending_or_sent(self):
        a = Assistant(MockClient(), "suspicious")
        a.handle("Why is my electric bill so high?", "t")
        self.assertEqual(a.pending, {})
        self.assertEqual(a.drafts, {})

    def test_paying_still_works_and_is_not_hijacked(self):
        r = self.ask("normal", "pay my electric bill")
        self.assertEqual(r["tool"], "pay_bill")


if __name__ == "__main__":
    unittest.main()
