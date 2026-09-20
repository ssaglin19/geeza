"""Hybrid intent router: Laya for 3 classes, keywords for the rest, LLM fallback.

The 3-class Laya model handles emergency, contact_family, handle_bills.
Keyword matching handles check_schedule, get_groceries, weather_check.
Everything else falls through to general_help (LLM/chat).

This is the v1 intent routing strategy: ship what works, fall back gracefully.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto


class IntentAction(Enum):
    LAUNCH_FLOW = auto()
    ASK_CLARIFY = auto()
    CHAT_FALLBACK = auto()
    EMERGENCY = auto()


@dataclass
class IntentResult:
    action: IntentAction
    skill: str
    flow_id: str | None
    message: str
    confidence: float
    alternatives: list[str]


# Confidence bands
ACT_THRESHOLD = 0.75
CLARIFY_THRESHOLD = 0.45

# Flow registry
SKILL_FLOWS = {
    "handle_bills": "consumers-energy-pay",
    "get_groceries": "kroger-grocery-order",
}

# Keyword patterns for non-Laya skills
KEYWORD_PATTERNS = {
    "check_schedule": [
        r"\b(calendar|schedule|appointment|meeting|event)\b",
        r"\b(what.*(today|tomorrow|this week)|when.*(appointment|meeting))\b",
        r"\b(do i have|am i free|what am i doing)\b",
        r"\b(remind me|reminder|don't let me forget)\b",
        r"\b(medication|pill|medicine|take my)\b",
    ],
    "get_groceries": [
        r"\b(groceries|grocery|food|shopping|store)\b",
        r"\b(order|buy|get|pick up).*(milk|bread|eggs|food|groceries)\b",
        r"\b(kroger|meijer|walmart|costco)\b",
        r"\b(we're out of|need more|running low on)\b",
    ],
    "weather_check": [
        r"\b(weather|temperature|rain|snow|sunny|cold|hot|jacket|umbrella)\b",
        r"\b(how (cold|hot)|what.*(weather|temperature))\b",
        r"\b(do i need|should i bring|will it)\b.*(rain|snow|cold|hot)\b",
    ],
}


def _keyword_match(text: str) -> tuple[str, float] | None:
    """Check keyword patterns. Returns (skill, confidence) or None."""
    text_lower = text.lower()
    for skill, patterns in KEYWORD_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return (skill, 0.85)  # High confidence for keyword match
    return None


def route_intent(
    laya_skill: str,
    laya_confidence: float,
    laya_probs: dict[str, float],
    text: str,
    available_flows: set[str] | None = None,
) -> IntentResult:
    """Hybrid routing: Laya for 3 classes, keywords for others, LLM fallback.

    Args:
        laya_skill: Laya's top prediction (emergency, contact_family, handle_bills)
        laya_confidence: Laya's confidence in that prediction
        laya_probs: Full probability distribution from Laya
        text: Original user utterance (for keyword matching)
        available_flows: Set of flow_ids that exist on this device

    Returns:
        IntentResult with action, skill, flow_id, message, confidence
    """
    available_flows = available_flows or set()

    # Emergency always wins, regardless of confidence
    if laya_skill == "emergency":
        return IntentResult(
            action=IntentAction.EMERGENCY,
            skill="emergency",
            flow_id=None,
            message="Getting help now.",
            confidence=laya_confidence,
            alternatives=[],
        )

    # Check keyword patterns first for non-Laya skills
    keyword_result = _keyword_match(text)
    if keyword_result:
        skill, kw_confidence = keyword_result
        flow_id = SKILL_FLOWS.get(skill)
        has_flow = flow_id is not None and flow_id in available_flows

        if has_flow and kw_confidence >= ACT_THRESHOLD:
            return IntentResult(
                action=IntentAction.LAUNCH_FLOW,
                skill=skill,
                flow_id=flow_id,
                message=f"I'll help you {skill.replace('_', ' ')}.",
                confidence=kw_confidence,
                alternatives=[],
            )
        elif has_flow:
            return IntentResult(
                action=IntentAction.ASK_CLARIFY,
                skill=skill,
                flow_id=flow_id,
                message=f"Did you want to {skill.replace('_', ' ')}?",
                confidence=kw_confidence,
                alternatives=[],
            )
        else:
            return IntentResult(
                action=IntentAction.CHAT_FALLBACK,
                skill=skill,
                flow_id=None,
                message=f"I can't {skill.replace('_', ' ')} yet, but I can help with other things.",
                confidence=kw_confidence,
                alternatives=[],
            )

    # Laya 3-class routing
    flow_id = SKILL_FLOWS.get(laya_skill)
    has_flow = flow_id is not None and flow_id in available_flows

    if not has_flow:
        return IntentResult(
            action=IntentAction.CHAT_FALLBACK,
            skill=laya_skill,
            flow_id=None,
            message=f"I can't {laya_skill.replace('_', ' ')} yet, but I can help with other things.",
            confidence=laya_confidence,
            alternatives=[],
        )

    if laya_confidence >= ACT_THRESHOLD:
        return IntentResult(
            action=IntentAction.LAUNCH_FLOW,
            skill=laya_skill,
            flow_id=flow_id,
            message=f"I'll help you {laya_skill.replace('_', ' ')}.",
            confidence=laya_confidence,
            alternatives=[],
        )

    if laya_confidence >= CLARIFY_THRESHOLD:
        # Find alternatives from Laya probs
        alternatives = [
            s for s, p in sorted(laya_probs.items(), key=lambda x: -x[1])
            if s != laya_skill and p > 0.1
        ][:2]
        return IntentResult(
            action=IntentAction.ASK_CLARIFY,
            skill=laya_skill,
            flow_id=flow_id,
            message=f"Did you want to {laya_skill.replace('_', ' ')}?",
            confidence=laya_confidence,
            alternatives=alternatives,
        )

    # Low confidence → chat fallback
    return IntentResult(
        action=IntentAction.CHAT_FALLBACK,
        skill=laya_skill,
        flow_id=None,
        message="I'm not sure what you need. Can you tell me more?",
        confidence=laya_confidence,
        alternatives=[],
    )
