import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT))
from boosh_flow import assist
from boosh_flow.nebius import NebiusClient
from gateway import demo_data
from gateway.assistant import Assistant


class Stub:
    """Client stub returning a fixed completion."""
    def __init__(self, text): self.text, self.last_model, self.used_fallback = text, "stub", False
    def complete(self, messages, **kw): return self.text


class TestScam(unittest.TestCase):
    def test_rules_flag_scam_fixture(self):
        self.assertTrue(assist.rule_screen(demo_data.EMAILS[2]))
        for e in demo_data.EMAILS[:2] + demo_data.EMAILS[3:]:
            self.assertEqual(assist.rule_screen(e), [], e["subject"])

    def test_model_cannot_clear_a_rule_hit(self):
        out = assist.scam_screen(demo_data.EMAILS[2], Stub(json.dumps({"is_scam": False, "confidence": 0.99})))
        self.assertTrue(out["flagged"])

    def test_model_can_raise_a_warning(self):
        out = assist.scam_screen(demo_data.EMAILS[0], Stub(json.dumps({"is_scam": True, "confidence": 0.9, "reasons": ["odd"]})))
        self.assertTrue(out["flagged"])

    def test_spoofed_sender_domain_flagged(self):
        e = {"from": "x <a@evil.test>", "subject": "hi", "body": "hello", "claims_to_be_domain": "bank.com"}
        self.assertTrue(assist.rule_screen(e))

    def test_flagged_mail_never_read_aloud(self):
        out = assist.read_back(demo_data.EMAILS[2], Stub("SSN please"))
        self.assertTrue(out["contents_withheld"])
        self.assertNotIn("gift", out["spoken"].lower())


class TestAssistant(unittest.TestCase):
    def make(self, scenario="normal"):
        return Assistant(NebiusClient(api_key=""), scenario)

    def test_happy_bill_path_needs_two_yes(self):
        a = self.make()
        r = a.handle("pay the electric bill"); self.assertEqual(r["actions"][0]["type"], "flow_offer")
        r = a.handle("yes"); self.assertEqual(r["actions"][0]["type"], "approval")
        r = a.handle("yes"); self.assertEqual(r["actions"][0]["type"], "paid")

    def test_nothing_paid_before_final_yes(self):
        a = self.make()
        a.handle("pay the electric bill")
        r = a.handle("yes")
        self.assertFalse(any(e["event"] == "FLOW_COMPLETE" for e in r["events"]))

    def test_suspicious_amount_stops_before_approval(self):
        a = self.make("suspicious")
        a.handle("pay the electric bill")
        r = a.handle("yes")
        self.assertEqual(r["actions"][0]["type"], "escalate")
        self.assertFalse(any(e["event"] == "APPROVAL_REQUIRED" for e in r["events"]))

    def test_other_text_cancels_pending_approval(self):
        a = self.make()
        a.handle("pay the electric bill"); a.handle("yes")
        a.handle("what is the weather")
        r = a.handle("yes")
        self.assertNotIn("paid", [x["type"] for x in r["actions"]])

    def test_amount_change_between_quote_and_yes_blocks_payment(self):
        a = self.make()
        a.handle("pay the electric bill"); a.handle("yes")
        a.scenario = "suspicious"  # vendor amount moved after the person was quoted
        a.pending["demo"]["amount"] = "86.90"
        r = a.handle("yes")
        self.assertNotIn("paid", [x["type"] for x in r["actions"]])

    def test_mail_flags_scam_only(self):
        r = self.make().handle("check my mail")
        flags = [i["scam"] for i in r["actions"][0]["items"]]
        self.assertEqual(flags, [False, False, True, False])


if __name__ == "__main__":
    unittest.main()
