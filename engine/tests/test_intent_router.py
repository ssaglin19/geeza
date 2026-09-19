"""Tests for intent routing."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from boosh_flow.intent_router import (
    IntentAction,
    route_intent,
    route_from_laya,
    ACT_THRESHOLD,
    CLARIFY_THRESHOLD,
)


class TestEmergency(unittest.TestCase):
    def test_emergency_bypasses_confidence(self):
        result = route_intent("emergency", 0.3, {"emergency": 0.3})
        self.assertEqual(result.action, IntentAction.EMERGENCY)
        self.assertIn("help", result.message.lower())

    def test_emergency_high_confidence(self):
        result = route_intent("emergency", 0.95, {"emergency": 0.95})
        self.assertEqual(result.action, IntentAction.EMERGENCY)


class TestLaunchFlow(unittest.TestCase):
    def test_high_confidence_with_flow_launches(self):
        result = route_intent(
            "pay_bill", 0.92, {"pay_bill": 0.92},
            available_flows={"consumers-energy-pay"},
        )
        self.assertEqual(result.action, IntentAction.LAUNCH_FLOW)
        self.assertEqual(result.flow_id, "consumers-energy-pay")

    def test_high_confidence_no_flow_falls_back(self):
        result = route_intent(
            "grocery_order", 0.92, {"grocery_order": 0.92},
            available_flows=set(),
        )
        self.assertEqual(result.action, IntentAction.CHAT_FALLBACK)


class TestClarify(unittest.TestCase):
    def test_medium_confidence_asks(self):
        result = route_intent(
            "pay_bill", 0.72,
            {"pay_bill": 0.72, "check_calendar": 0.15, "read_email": 0.08},
        )
        self.assertEqual(result.action, IntentAction.ASK_CLARIFY)
        self.assertIn("pay bill", result.message.lower())
        self.assertIn("check calendar", result.message.lower())

    def test_clarify_includes_alternatives(self):
        result = route_intent(
            "pay_bill", 0.65,
            {"pay_bill": 0.65, "check_calendar": 0.20, "read_email": 0.10},
            available_flows={"consumers-energy-pay"},
        )
        self.assertEqual(result.action, IntentAction.ASK_CLARIFY)
        self.assertIn("check_calendar", result.alternatives)


class TestFallback(unittest.TestCase):
    def test_low_confidence_falls_back(self):
        result = route_intent("pay_bill", 0.45, {"pay_bill": 0.45})
        self.assertEqual(result.action, IntentAction.CHAT_FALLBACK)
        self.assertIn("not sure", result.message.lower())

    def test_unknown_skill_falls_back(self):
        result = route_intent("nonexistent_skill", 0.90, {"nonexistent_skill": 0.90})
        self.assertEqual(result.action, IntentAction.CHAT_FALLBACK)


class TestFromLaya(unittest.TestCase):
    def test_routes_from_laya_output(self):
        laya_result = {
            "answers": {
                "intent": {
                    "choice": "pay_bill",
                    "confidence": 0.92,
                    "probabilities": {"pay_bill": 0.92, "check_calendar": 0.05},
                }
            }
        }
        result = route_from_laya(laya_result, available_flows={"consumers-energy-pay"})
        self.assertEqual(result.action, IntentAction.LAUNCH_FLOW)
        self.assertEqual(result.skill, "pay_bill")


class TestBandEdges(unittest.TestCase):
    def test_act_threshold(self):
        result = route_intent(
            "pay_bill", ACT_THRESHOLD,
            {"pay_bill": ACT_THRESHOLD},
            available_flows={"consumers-energy-pay"},
        )
        self.assertEqual(result.action, IntentAction.LAUNCH_FLOW)

    def test_just_below_act_threshold(self):
        result = route_intent(
            "pay_bill", ACT_THRESHOLD - 0.01,
            {"pay_bill": ACT_THRESHOLD - 0.01},
        )
        self.assertEqual(result.action, IntentAction.ASK_CLARIFY)

    def test_clarify_threshold(self):
        result = route_intent(
            "pay_bill", CLARIFY_THRESHOLD,
            {"pay_bill": CLARIFY_THRESHOLD},
        )
        self.assertEqual(result.action, IntentAction.ASK_CLARIFY)

    def test_just_below_clarify_threshold(self):
        result = route_intent(
            "pay_bill", CLARIFY_THRESHOLD - 0.01,
            {"pay_bill": CLARIFY_THRESHOLD - 0.01},
        )
        self.assertEqual(result.action, IntentAction.CHAT_FALLBACK)


if __name__ == "__main__":
    unittest.main()
