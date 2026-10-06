"""Nemotron-backed assistant skills: scam screen, mail read-back, chat.

Division of labor: the model reads and explains. Code decides. A deterministic
scam check runs first and the model can only add a warning, never clear one.
Money moves only through the flow engine's approval gate (engine.py), which no
model output can bypass.
"""
from __future__ import annotations

import json
import re

from . import decider

SCAM_SYSTEM = (
    "You screen email for an older adult. Reply with JSON only: "
    '{"is_scam": bool, "confidence": 0..1, "reasons": [short strings]}. '
    "A scam asks for money, gift cards, passwords, codes or personal numbers, or pressures the reader to act now."
)
EXPLAIN_SYSTEM = (
    "You read email aloud for an older adult. Use plain words, 3 short sentences at most. "
    "Say who it is from, what it wants, and whether anything needs doing. Never repeat links."
)
CHAT_SYSTEM = (
    "You are Geeza, a calm helper for an older adult. Short plain sentences, one step at a time. "
    "You cannot move money. Payments go through a separate approval screen the person controls."
)

_RULES = [
    (r"gift\s*card|itunes card|google play card", "asks for gift cards"),
    (r"wire (transfer|money)|western union|crypto|bitcoin", "asks for a wire or crypto"),
    (r"password|social security|ssn|one[- ]time (code|passcode)|verification code", "asks for credentials or ID numbers"),
    (r"act now|immediately|within 24 hours|final notice|suspended|will be closed", "pressures you to act now"),
]


def _domain(addr: str) -> str:
    return addr.rsplit("@", 1)[-1].lower().strip(" >") if "@" in addr else ""


def rule_screen(email: dict) -> list[str]:
    """Deterministic scam signals. Pure code, no model."""
    text = f"{email.get('subject', '')} {email.get('body', '')}".lower()
    reasons = [why for pat, why in _RULES if re.search(pat, text)]
    sender, claimed = _domain(email.get("from", "")), email.get("claims_to_be_domain", "")
    if claimed and sender and not (sender == claimed or sender.endswith("." + claimed)):
        reasons.append(f"claims to be {claimed} but came from {sender}")
    return reasons


def _parse_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except ValueError:
        return {}


def _conf(out: dict) -> float:
    try:
        return float(out.get("confidence", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def scam_screen(email: dict, client) -> dict:
    """Return {flagged, reasons, rule_hits, model_flag, model_used, fallback, decision}.

    Code rules run first. The model (typed scam-screen pack, bands from the pack) can raise a
    warning, never clear a rule hit."""
    rule_hits = rule_screen(email)
    msg = f"From: {email.get('from', '')}\nSubject: {email.get('subject', '')}\n\n{email.get('body', '')}"
    d = decider.decide("scam-screen", msg, client)
    decision = None
    if d["ok"]:
        decision = decider.scam_policy(d["answers"])
        model_flag = decision["warn"]
        reasons = list(rule_hits)
        a = d["answers"]
        for key, why in (("requests_payment", "asks for money"), ("requests_credentials", "asks for passwords or codes"),
                         ("urgency_pressure", "pressures you to act now"), ("impersonates_authority", "claims to be an official sender")):
            if model_flag and a[key]["p"] >= 0.5 and why not in reasons:
                reasons.append(why)
        soft = decision["soft"] and not model_flag
    else:
        # Typed pack unavailable or malformed: keep the earlier single-JSON check.
        out = _parse_json(client.complete(
            [{"role": "system", "content": SCAM_SYSTEM}, {"role": "user", "content": msg}], max_tokens=200, temperature=0.0))
        model_flag = bool(out.get("is_scam")) and _conf(out) >= 0.85  # spec act band
        reasons = list(rule_hits)
        if model_flag:
            reasons += [r for r in out.get("reasons", []) if isinstance(r, str) and r not in reasons]
        soft = False
    return {
        "flagged": bool(rule_hits) or model_flag,  # model can raise, never clear
        "reasons": reasons,
        "rule_hits": rule_hits,
        "model_flag": model_flag,
        "soft_warning": soft and not rule_hits,
        "decision": decision,
        "model_used": getattr(client, "last_model", None),
        "fallback": bool(getattr(client, "used_fallback", False)),
    }


def read_back(email: dict, client) -> dict:
    """Scam screen first. A flagged message is never read aloud, only warned about.

    Then the mail-triage pack picks a category (bill, medical, personal, junk, scam), urgency and
    whether a reply is expected. Its bands (pack JSON): high >= 0.85 act; 0.60-0.85 hedge;
    below 0.60 read the subject and sender only."""
    screen = scam_screen(email, client)
    warn = ("This looks like a scam. Do not reply or click anything. Ask Sean to look at it first.")
    if screen["flagged"]:
        return {"screen": screen, "spoken": warn, "contents_withheld": True, "triage": None}
    msg = f"From: {email.get('from', '')}\nSubject: {email.get('subject', '')}\n\n{email.get('body', '')}"
    d = decider.decide("mail-triage", msg, client)
    triage = decider.mail_policy(d["answers"]) if d["ok"] else None
    if triage and triage["scam"]:  # the triage pack can also raise the warning
        screen["flagged"] = True
        screen["reasons"] = screen["reasons"] + ["mail triage marks it as a scam"]
        return {"screen": screen, "spoken": warn, "contents_withheld": True, "triage": triage}
    if triage and triage["category"] == "junk" and triage["band"] == "high":
        return {"screen": screen, "spoken": "Junk mail, I skipped it.", "contents_withheld": False, "triage": triage}
    if triage and triage["band"] == "low":
        return {"screen": screen, "contents_withheld": False, "triage": triage,
                "spoken": f"I am not sure what this is. From {email.get('from', 'unknown')}: {email.get('subject', '')}."}
    spoken = client.complete(
        [{"role": "system", "content": EXPLAIN_SYSTEM}, {"role": "user", "content": msg}], max_tokens=200)
    if triage and triage["band"] == "medium":
        spoken = f"This looks like {('a ' if triage['category'] != 'junk' else '')}{triage['category']} message. " + spoken
    screen["fallback"] = screen["fallback"] or bool(getattr(client, "used_fallback", False))
    return {"screen": screen, "spoken": spoken, "contents_withheld": False, "triage": triage}


def chat(history: list[dict], client, memory: str = "") -> dict:
    msgs = [{"role": "system", "content": CHAT_SYSTEM + ("\n\n" + memory if memory else "")}] + [
        {"role": m["role"], "content": m["content"]} for m in history[-10:]
        if m.get("role") in ("user", "assistant")]
    reply = client.complete(msgs, max_tokens=300)
    return {"reply": reply, "model_used": getattr(client, "last_model", None),
            "fallback": bool(getattr(client, "used_fallback", False))}
