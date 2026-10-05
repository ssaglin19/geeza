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


class TestTools(unittest.TestCase):
    def setUp(self):
        from boosh_flow import tools
        self.tools = tools

    def test_parse_valid_call(self):
        c = self.tools.parse_call('ok {"tool": "set_reminder", "args": {"what": "pills", "when": "8am"}}')
        self.assertEqual(c, {"tool": "set_reminder", "args": {"what": "pills", "when": "8am"}})

    def test_unknown_tool_rejected(self):
        c = self.tools.parse_call('{"tool": "wire_money", "args": {"to": "x"}}')
        self.assertNotIn("tool", c)

    def test_missing_or_nonstring_args_rejected(self):
        self.assertNotIn("tool", self.tools.parse_call('{"tool": "set_reminder", "args": {"what": "pills"}}'))
        self.assertNotIn("tool", self.tools.parse_call('{"tool": "tell_caregiver", "args": {"note": 5}}'))

    def test_junk_and_extra_args_never_raise(self):
        self.assertEqual(self.tools.parse_call("hello"), {"reply": "hello"})
        c = self.tools.parse_call('{"tool": "pay_bill", "args": {"amount": "9999", "approved": "true"}}')
        self.assertEqual(c, {"tool": "pay_bill", "args": {}})  # unknown args dropped, no approval flag exists

    def test_acting_tools_flagged(self):
        acts = {n for n, t in self.tools.REGISTRY.items() if t.acts}
        self.assertEqual(acts, {"pay_bill", "set_reminder", "tell_caregiver"})


class TestToolLoop(unittest.TestCase):
    def make(self): return Assistant(NebiusClient(api_key=""))

    def test_reminder_needs_yes(self):
        a = self.make()
        r = a.handle("remind me to take my pills at 8am")
        self.assertEqual(r["actions"][0]["type"], "confirm")
        self.assertEqual(a.reminders, {})
        r = a.handle("yes")
        self.assertEqual(r["actions"][0]["type"], "reminder_set")
        self.assertEqual(len(a.reminders["demo"]), 1)

    def test_reminder_not_saved_if_declined(self):
        a = self.make()
        a.handle("remind me to call Ruth at 5pm"); a.handle("no")
        self.assertEqual(a.reminders, {})

    def test_caregiver_note_is_draft_only(self):
        a = self.make()
        a.handle("tell Sean I need groceries")
        r = a.handle("yes")
        self.assertEqual(r["actions"][0]["type"], "draft_saved")
        self.assertIn("not been sent", r["response"])

    def test_scam_check_on_pasted_text(self):
        a = self.make()
        r = a.handle("Is this a scam? Your account is suspended, buy gift cards now to fix it")
        self.assertTrue(r["actions"][0]["flagged"])

    def test_live_model_cannot_skip_yes(self):
        class Live:
            live, used_fallback, last_model = True, False, "m"
            def complete(self, messages, **kw):
                return '{"tool": "set_reminder", "args": {"what": "pills", "when": "8am"}}'
        a = Assistant(Live())
        r = a.handle("anything")
        self.assertEqual(r["actions"][0]["type"], "confirm")
        self.assertEqual(a.reminders, {})
