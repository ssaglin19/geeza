"""Route Laya intent classification to skills and flows.

Takes Laya's choice answer (which skill) and returns an action: launch a flow,
ask a clarifying question, or fall back to general chat. The flow engine
(System 0) handles execution; this is the System 1 → System 0 bridge.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class IntentAction(Enum):
    LAUNCH_FLOW = auto()   # high confidence, flow exists
    ASK_CLARIFY = auto()   # medium confidence, confirm intent
    CHAT_FALLBACK = auto() # low confidence or no flow, general conversation
    EMERGENCY = auto()     # emergency skill, immediate escalation


@dataclass
class IntentResult:
    action: IntentAction
    skill: str
    flow_id: str | None
    message: str
    confidence: float
    alternatives: list


# Skill → flow mapping. Flow IDs match flows/*.json files.
SKILL_FLOWS = {
    "pay_bill": "consumers-energy-pay",  # placeholder; real flows registered per user
    "grocery_order": None,               # no flow yet
    "check_calendar": None,
    "read_email": None,
    "call_family": None,
    "medication_reminder": None,
    "weather_check": None,
    "scam_check": None,
    "general_question": None,
    "emergency": None,
}

# Confidence bands (from laya/questions/intent-routing.json usage section)
ACT_THRESHOLD = 0.85
CLARIFY_THRESHOLD = 0.60


def route_intent(
    skill: str,
    confidence: float,
    probabilities: dict,
    available_flows: set | None = None,
) -> IntentResult:
    """Route a Laya intent classification to an action.

    Args:
        skill: the chosen skill label
        confidence: Laya's confidence in the choice
        probabilities: full probability distribution over skills
        available_flows: set of flow_ids that exist for this user (None = all)

    Returns:
        IntentResult with action, flow_id (if launching), and voice message.
    """
    if available_flows is None:
        available_flows = set(SKILL_FLOWS.values()) - {None}

    # Emergency bypasses all confidence checks
    if skill == "emergency":
        return IntentResult(
            action=IntentAction.EMERGENCY,
            skill=skill,
            flow_id=None,
            message="I'm calling for help now.",
            confidence=confidence,
            alternatives=[],
        )

    flow_id = SKILL_FLOWS.get(skill)
    has_flow = flow_id is not None and flow_id in available_flows

    # No flow for this skill → nothing to launch or clarify, go to chat
    if not has_flow:
        return IntentResult(
            action=IntentAction.CHAT_FALLBACK,
            skill=skill,
            flow_id=None,
            message=f"I can't {skill.replace('_', ' ')} yet, but I can help with other things.",
            confidence=confidence,
            alternatives=[],
        )

    # High confidence + flow exists → launch
    if confidence >= ACT_THRESHOLD:
        return IntentResult(
            action=IntentAction.LAUNCH_FLOW,
            skill=skill,
            flow_id=flow_id,
            message=f"I'll help you {skill.replace('_', ' ')}.",
            confidence=confidence,
            alternatives=[],
        )

    # Medium confidence → ask to confirm
    if confidence >= CLARIFY_THRESHOLD:
        # Find the second-best alternative
        sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        alternatives = [s for s, p in sorted_probs[1:3] if p > 0.1]
        alt_text = f" or {alternatives[0].replace('_', ' ')}" if alternatives else ""
        return IntentResult(
            action=IntentAction.ASK_CLARIFY,
            skill=skill,
            flow_id=None,
            message=f"Did you want to {skill.replace('_', ' ')}{alt_text}?",
            confidence=confidence,
            alternatives=alternatives,
        )

    # Low confidence or no flow → chat fallback
    return IntentResult(
        action=IntentAction.CHAT_FALLBACK,
        skill=skill,
        flow_id=None,
        message="I'm not sure what you need. Can you tell me more?",
        confidence=confidence,
        alternatives=[],
    )


def route_from_laya(laya_result: dict, available_flows: set | None = None) -> IntentResult:
    """Route from Laya's raw predict() output.

    Expects the intent-routing question pack format:
      {"answers": {"intent": {"choice": "pay_bill", "confidence": 0.92,
                              "probabilities": {"pay_bill": 0.92, ...}}}}
    """
    answer = laya_result["answers"]["intent"]
    return route_intent(
        skill=answer["choice"],
        confidence=answer["confidence"],
        probabilities=answer.get("probabilities", {}),
        available_flows=available_flows,
    )
