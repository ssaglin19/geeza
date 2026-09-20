"""Tests for the hybrid intent router."""
import unittest

from boosh_flow.intent_router_hybrid import (
    IntentAction,
    route_intent,
    _keyword_match,
)


class TestKeywordMatch(unittest.TestCase):
    def test_schedule_keywords(self):
        result = _keyword_match("What's on my calendar today")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "check_schedule")

    def test_grocery_keywords(self):
        result = _keyword_match("I need to order groceries from Kroger")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "get_groceries")

    def test_weather_keywords(self):
        result = _keyword_match("Do I need a jacket today")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "weather_check")

    def test_no_match(self):
        result = _keyword_match("I need to pay the electric bill")
        self.assertIsNone(result)


class TestHybridRouting(unittest.TestCase):
    def test_emergency_bypasses_everything(self):
        result = route_intent(
            "emergency", 0.3, {"emergency": 0.3, "handle_bills": 0.7},
            "I need to pay the electric bill",
        )
        self.assertEqual(result.action, IntentAction.EMERGENCY)

    def test_keyword_match_launches_flow(self):
        result = route_intent(
            "handle_bills", 0.5, {"handle_bills": 0.5},
            "What's on my calendar today",
            available_flows={"kroger-grocery-order"},
        )
        # Keyword match for schedule, but no flow for schedule → chat fallback
        self.assertEqual(result.action, IntentAction.CHAT_FALLBACK)
        self.assertEqual(result.skill, "check_schedule")

    def test_keyword_groceries_with_flow(self):
        result = route_intent(
            "handle_bills", 0.5, {"handle_bills": 0.5},
            "I need to order groceries from Kroger",
            available_flows={"kroger-grocery-order"},
        )
        self.assertEqual(result.action, IntentAction.LAUNCH_FLOW)
        self.assertEqual(result.skill, "get_groceries")
        self.assertEqual(result.flow_id, "kroger-grocery-order")

    def test_laya_high_confidence_launches(self):
        result = route_intent(
            "handle_bills", 0.85, {"handle_bills": 0.85},
            "I need to pay the electric bill",
            available_flows={"consumers-energy-pay"},
        )
        self.assertEqual(result.action, IntentAction.LAUNCH_FLOW)
        self.assertEqual(result.skill, "handle_bills")
        self.assertEqual(result.flow_id, "consumers-energy-pay")

    def test_laya_medium_confidence_asks(self):
        result = route_intent(
            "handle_bills", 0.6, {"handle_bills": 0.6, "contact_family": 0.3},
            "I need to pay the electric bill",
            available_flows={"consumers-energy-pay"},
        )
        self.assertEqual(result.action, IntentAction.ASK_CLARIFY)
        self.assertIn("contact_family", result.alternatives)

    def test_laya_low_confidence_falls_back(self):
        result = route_intent(
            "handle_bills", 0.3, {"handle_bills": 0.3},
            "I need to pay the electric bill",
            available_flows={"consumers-energy-pay"},
        )
        self.assertEqual(result.action, IntentAction.CHAT_FALLBACK)

    def test_no_flow_falls_back(self):
        result = route_intent(
            "contact_family", 0.9, {"contact_family": 0.9},
            "Call my son Sean",
            available_flows=set(),
        )
        self.assertEqual(result.action, IntentAction.CHAT_FALLBACK)


if __name__ == "__main__":
    unittest.main()
