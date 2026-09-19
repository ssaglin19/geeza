"""Caregiver escalation: what happens when the assistant can't proceed.

Every failure mode in the system ends here: flow aborts, low-confidence
decisions, scam detections, emergency intents. The escalation path logs the
event, notifies the caregiver, and tells the user what to do next.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path


class EscalationReason(Enum):
    FLOW_ABORTED = auto()        # flow engine aborted (page unrecognized, gate failed, etc.)
    LOW_CONFIDENCE = auto()      # Laya or page match below threshold
    SCAM_DETECTED = auto()       # scam screen flagged a message
    EMERGENCY = auto()           # user said "help" / "emergency"
    APPROVAL_DENIED = auto()     # user said no at the approval gate
    PAGE_DRIFT = auto()          # site redesign detected (page_loop or repeated unrecognized)


@dataclass
class EscalationEvent:
    reason: EscalationReason
    timestamp: float
    context: dict = field(default_factory=dict)
    user_message: str = ""
    caregiver_message: str = ""


class EscalationLog:
    """Append-only log of escalation events. Local JSONL, one line per event."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: EscalationEvent):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "reason": event.reason.name,
                "timestamp": event.timestamp,
                "context": event.context,
                "user_message": event.user_message,
                "caregiver_message": event.caregiver_message,
            }) + "\n")

    def recent(self, n: int = 10) -> list:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").strip().splitlines()
        return [json.loads(l) for l in lines[-n:]]


# Voice messages for the user, per reason
USER_MESSAGES = {
    EscalationReason.FLOW_ABORTED:
        "I ran into a problem with that. Let me get some help.",
    EscalationReason.LOW_CONFIDENCE:
        "I'm not sure about this one. Let me check with someone.",
    EscalationReason.SCAM_DETECTED:
        "This looks like a scam. Don't click anything or call any numbers. "
        "I'll let your family know.",
    EscalationReason.EMERGENCY:
        "I'm calling for help now. Stay on the line.",
    EscalationReason.APPROVAL_DENIED:
        "Okay, I've cancelled that. Is there something else I can help with?",
    EscalationReason.PAGE_DRIFT:
        "The website looks different than I expected. Let me get some help.",
}

# Caregiver notification messages, per reason
CAREGIVER_MESSAGES = {
    EscalationReason.FLOW_ABORTED:
        "Boosh flow aborted: {detail}. Check the trace log for details.",
    EscalationReason.LOW_CONFIDENCE:
        "Boosh uncertain: {detail}. May need your input.",
    EscalationReason.SCAM_DETECTED:
        "SCAM ALERT: Boosh flagged a message as suspicious. "
        "Subject: {subject}. Recommend calling to check in.",
    EscalationReason.EMERGENCY:
        "EMERGENCY: User requested help. Call immediately.",
    EscalationReason.APPROVAL_DENIED:
        "User declined approval for {flow}. No action taken.",
    EscalationReason.PAGE_DRIFT:
        "Site redesign detected for {flow}. Flow may need updating.",
}


def escalate(
    reason: EscalationReason,
    log: EscalationLog,
    context: dict | None = None,
    detail: str = "",
    subject: str = "",
    flow: str = "",
) -> EscalationEvent:
    """Create and log an escalation event.

    Returns the event with user_message and caregiver_message filled in.
    The caller is responsible for delivering the caregiver notification
    (local notification, push, etc.) and speaking the user message.
    """
    context = context or {}
    caregiver_msg = CAREGIVER_MESSAGES[reason].format(
        detail=detail, subject=subject, flow=flow,
    )
    event = EscalationEvent(
        reason=reason,
        timestamp=time.time(),
        context=context,
        user_message=USER_MESSAGES[reason],
        caregiver_message=caregiver_msg,
    )
    log.record(event)
    return event
