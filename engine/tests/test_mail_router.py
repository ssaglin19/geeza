"""Tests for the mail read-back router."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from boosh_flow.mail_router import Behavior, MailDecision, route, summarize_for_voice


def _answers(category="bill", cat_conf=0.9, urgency=0.5, needs_reply=0.3, is_scam=0.05):
    return {
        "category": {"choice": category, "confidence": cat_conf},
        "urgency": {"score": urgency},
        "needs_reply": {"noul": needs_reply},
        "is_scam": {"noul": is_scam},
    }


class TestScamDetection(unittest.TestCase):
    def test_high_scam_probability_flags(self):
        d = route(_answers(is_scam=0.92))
        self.assertEqual(d.behavior, Behavior.FLAG_SCAM)

    def test_category_scam_flags(self):
        d = route(_answers(category="scam", cat_conf=0.88))
        self.assertEqual(d.behavior, Behavior.FLAG_SCAM)

    def test_scam_never_reads_contents(self):
        d = route(_answers(is_scam=0.95))
        msg = summarize_for_voice(d, "Click here to verify your account")
        self.assertNotIn("Click here", msg)
        self.assertIn("scam", msg.lower())


class TestJunkHandling(unittest.TestCase):
    def test_high_confidence_junk_skips(self):
        d = route(_answers(category="junk", cat_conf=0.90))
        self.assertEqual(d.behavior, Behavior.SKIP)

    def test_low_confidence_junk_asks(self):
        d = route(_answers(category="junk", cat_conf=0.55))
        self.assertEqual(d.behavior, Behavior.ASK_USER)


class TestKnownCategories(unittest.TestCase):
    def test_high_confidence_bill_summarizes(self):
        d = route(_answers(category="bill", cat_conf=0.92))
        self.assertEqual(d.behavior, Behavior.SUMMARIZE)

    def test_high_urgency_mentions_it(self):
        d = route(_answers(category="medical", cat_conf=0.90, urgency=1.8))
        self.assertEqual(d.behavior, Behavior.SUMMARIZE)
        self.assertIn("urgency", d.reason)

    def test_medium_confidence_hedges(self):
        d = route(_answers(category="bill", cat_conf=0.70))
        self.assertEqual(d.behavior, Behavior.SUMMARIZE)
        self.assertIn("hedge", d.reason)

    def test_low_confidence_reads_full(self):
        d = route(_answers(category="bill", cat_conf=0.45))
        self.assertEqual(d.behavior, Behavior.READ_FULL)


class TestVoiceOutput(unittest.TestCase):
    def test_scam_message_is_safe(self):
        d = route(_answers(is_scam=0.95))
        msg = summarize_for_voice(d, "malicious content")
        self.assertIn("Do not click", msg)

    def test_skip_message_is_brief(self):
        d = route(_answers(category="junk", cat_conf=0.90))
        msg = summarize_for_voice(d, "Buy now!")
        self.assertIn("Skipping", msg)

    def test_ask_user_message(self):
        d = route(_answers(category="junk", cat_conf=0.55))
        msg = summarize_for_voice(d, "Some email")
        self.assertIn("not sure", msg.lower())

    def test_read_full_includes_text(self):
        d = route(_answers(category="bill", cat_conf=0.45))
        msg = summarize_for_voice(d, "Your bill is $87.43")
        self.assertIn("$87.43", msg)


if __name__ == "__main__":
    unittest.main()
