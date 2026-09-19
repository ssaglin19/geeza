"""Mail read-back router: takes Laya's mail-triage output and decides what to do.

This is the bridge between System 1 (Laya's typed decisions) and the user
experience. It does NOT call Laya — it consumes the answers dict from
laya/questions/mail-triage.json and returns a behavior decision.

The app layer (iOS) calls Laya, gets the answers, passes them here, and
executes the returned behavior.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Behavior(Enum):
    SUMMARIZE = "summarize"       # read a short summary aloud
    READ_FULL = "read_full"       # read the whole email (personal, or low confidence)
    SKIP = "skip"                 # don't mention it (junk)
    FLAG_SCAM = "flag_scam"       # warn loudly, do not read contents
    ASK_USER = "ask_user"         # confidence too low, ask what to do


@dataclass
class MailDecision:
    behavior: Behavior
    reason: str
    category: str
    confidence: float
    urgency: float | None = None
    needs_reply: bool | None = None


def route(answers: dict, thresholds: dict | None = None) -> MailDecision:
    """Route a mail-triage result to a behavior.

    answers: the "answers" dict from Laya's predict() with the mail-triage
             question pack. Expected keys: category, urgency, needs_reply, is_scam.
    thresholds: optional overrides for confidence bands.
    """
    t = {
        "scam_high": 0.85,
        "category_high": 0.85,
        "category_medium": 0.60,
        "urgency_high": 1.5,
    }
    if thresholds:
        t.update(thresholds)

    cat = answers.get("category", {})
    category = cat.get("choice", "unknown")
    cat_conf = cat.get("confidence", 0.0)

    urgency = answers.get("urgency", {}).get("score", 0.0)
    needs_reply = answers.get("needs_reply", {}).get("noul", 0.0) > 0.5
    is_scam = answers.get("is_scam", {}).get("noul", 0.0)

    # --- scam check first: never read scam contents aloud ---
    if is_scam >= t["scam_high"] or category == "scam":
        return MailDecision(
            behavior=Behavior.FLAG_SCAM,
            reason=f"scam detected (P={is_scam:.2f}, category={category})",
            category=category,
            confidence=cat_conf,
            urgency=urgency,
            needs_reply=needs_reply,
        )

    # --- junk: skip unless confidence is low ---
    if category == "junk":
        if cat_conf >= t["category_high"]:
            return MailDecision(
                behavior=Behavior.SKIP,
                reason=f"junk with high confidence ({cat_conf:.2f})",
                category=category,
                confidence=cat_conf,
                urgency=urgency,
                needs_reply=needs_reply,
            )
        # low-confidence junk: treat as unknown, ask
        return MailDecision(
            behavior=Behavior.ASK_USER,
            reason=f"junk but low confidence ({cat_conf:.2f})",
            category=category,
            confidence=cat_conf,
            urgency=urgency,
            needs_reply=needs_reply,
        )

    # --- known categories with confidence bands ---
    if cat_conf >= t["category_high"]:
        # high confidence: summarize, mention urgency if high
        if urgency >= t["urgency_high"]:
            return MailDecision(
                behavior=Behavior.SUMMARIZE,
                reason=f"{category} with high urgency ({urgency:.1f})",
                category=category,
                confidence=cat_conf,
                urgency=urgency,
                needs_reply=needs_reply,
            )
        return MailDecision(
            behavior=Behavior.SUMMARIZE,
            reason=f"{category} with high confidence ({cat_conf:.2f})",
            category=category,
            confidence=cat_conf,
            urgency=urgency,
            needs_reply=needs_reply,
        )

    if cat_conf >= t["category_medium"]:
        # medium confidence: summarize but hedge
        return MailDecision(
            behavior=Behavior.SUMMARIZE,
            reason=f"{category} with medium confidence ({cat_conf:.2f}), hedge",
            category=category,
            confidence=cat_conf,
            urgency=urgency,
            needs_reply=needs_reply,
        )

    # low confidence: read the whole thing, let the user decide
    return MailDecision(
        behavior=Behavior.READ_FULL,
        reason=f"low confidence ({cat_conf:.2f}), reading verbatim",
        category=category,
        confidence=cat_conf,
        urgency=urgency,
        needs_reply=needs_reply,
    )


def summarize_for_voice(decision: MailDecision, email_text: str) -> str:
    """Generate the spoken output for a mail decision.

    This is a placeholder — the real implementation calls System 2 (Bonsai)
    to generate a natural summary. For now, it returns a template.
    """
    if decision.behavior == Behavior.FLAG_SCAM:
        return (
            "This email looks like a scam. I won't read it to you. "
            "Do not click any links or call any numbers in it. "
            "If you're worried, call the company directly using the number on your bill or card."
        )
    if decision.behavior == Behavior.SKIP:
        return "Skipping a promotional email."
    if decision.behavior == Behavior.ASK_USER:
        return (
            f"I think this might be {decision.category}, but I'm not sure. "
            "Do you want me to read it to you?"
        )
    if decision.behavior == Behavior.READ_FULL:
        return f"I'm not sure what this is, so I'll read it to you. {email_text}"
    # SUMMARIZE
    urgency_note = ""
    if decision.urgency and decision.urgency >= 1.5:
        urgency_note = " This seems important. "
    reply_note = ""
    if decision.needs_reply:
        reply_note = " You may want to reply. "
    return (
        f"You have a {decision.category} email.{urgency_note}{reply_note}"
        f"Here's a summary: [summary would be generated by Bonsai here]"
    )
