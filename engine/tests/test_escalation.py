"""Tests for caregiver escalation."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from boosh_flow.escalation import (
    EscalationLog,
    EscalationReason,
    escalate,
)


class TestEscalationLog(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl")
        self.tmp.close()
        self.log = EscalationLog(self.tmp.name)

    def tearDown(self):
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_record_and_read(self):
        event = escalate(EscalationReason.FLOW_ABORTED, self.log, detail="test abort")
        recent = self.log.recent(1)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["reason"], "FLOW_ABORTED")
        self.assertIn("test abort", recent[0]["caregiver_message"])

    def test_multiple_events(self):
        escalate(EscalationReason.FLOW_ABORTED, self.log, detail="first")
        escalate(EscalationReason.SCAM_DETECTED, self.log, subject="Fake IRS")
        recent = self.log.recent(10)
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0]["reason"], "FLOW_ABORTED")
        self.assertEqual(recent[1]["reason"], "SCAM_DETECTED")

    def test_recent_limits(self):
        for i in range(15):
            escalate(EscalationReason.LOW_CONFIDENCE, self.log, detail=f"event {i}")
        recent = self.log.recent(5)
        self.assertEqual(len(recent), 5)
        self.assertIn("event 14", recent[-1]["caregiver_message"])


class TestUserMessages(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl")
        self.tmp.close()
        self.log = EscalationLog(self.tmp.name)

    def tearDown(self):
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_scam_message_warns_user(self):
        event = escalate(EscalationReason.SCAM_DETECTED, self.log, subject="Fake Medicare")
        self.assertIn("scam", event.user_message.lower())
        self.assertIn("don't click", event.user_message.lower())

    def test_emergency_message_is_immediate(self):
        event = escalate(EscalationReason.EMERGENCY, self.log)
        self.assertIn("calling for help", event.user_message.lower())

    def test_approval_denied_is_graceful(self):
        event = escalate(EscalationReason.APPROVAL_DENIED, self.log, flow="pay-bill")
        self.assertIn("cancelled", event.user_message.lower())

    def test_page_drift_explains_problem(self):
        event = escalate(EscalationReason.PAGE_DRIFT, self.log, flow="consumers-energy-pay")
        self.assertIn("different", event.user_message.lower())


class TestCaregiverMessages(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl")
        self.tmp.close()
        self.log = EscalationLog(self.tmp.name)

    def tearDown(self):
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_scam_alert_includes_subject(self):
        event = escalate(EscalationReason.SCAM_DETECTED, self.log, subject="Fake IRS")
        self.assertIn("Fake IRS", event.caregiver_message)
        self.assertIn("SCAM ALERT", event.caregiver_message)

    def test_emergency_says_call_immediately(self):
        event = escalate(EscalationReason.EMERGENCY, self.log)
        self.assertIn("immediately", event.caregiver_message.lower())

    def test_page_drift_names_flow(self):
        event = escalate(EscalationReason.PAGE_DRIFT, self.log, flow="consumers-energy-pay")
        self.assertIn("consumers-energy-pay", event.caregiver_message)


if __name__ == "__main__":
    unittest.main()
