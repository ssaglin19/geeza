"""SIMULATED 911 dispatcher for the hackathon demo.

Nothing here can reach a real number: this module imports no network, phone or subprocess code,
and builds only a canned, clearly labelled transcript. The person sees that it is a simulation.
A real build would hand off to the phone's emergency call; that part is parked with the iOS work.
"""
from __future__ import annotations

import datetime
import re

# Words that go straight to the simulated dispatcher without asking the model. "help" counts only
# when it stands alone or is a plain cry for help ("help me", "I need help"), so "can you help me
# pay my bill" does not trigger it. Anything vaguer goes to the model's intent routing, which still
# sends real emergencies here.
_EMERGENCY = re.compile(
    r"\b911\b|\bemergency\b(?!\s+(?:contact|number|phone))|\b(?:i|i've|i have)\s+(?:fell(?!\s+(?:asleep|in love|behind|for))|fallen)\b|\bfell\s+(?:down|over)\b"
    r"|\bfallen and\b|\bcan(?:'|\u2019)?t\s+get\s+up\b|\bcannot\s+get\s+up\b|\bchest\s+pain\b|\bheart\s+attack\b"
    r"|\bcan(?:'|\u2019)?t\s+breathe\b|\bambulance\b|\bhaving\s+a\s+stroke\b",
    re.I)
_CRY_FOR_HELP = re.compile(
    r"^\W*(?:please\s+|somebody\s+|someone\s+|oh\s+)*(?:help(?:\s+me)?|i\s+need\s+help(?:\s+now)?|need\s+help(?:\s+now)?)(?:\s+please)?\W*$",
    re.I)


def is_emergency(text: str) -> bool:
    return bool(_EMERGENCY.search(text) or _CRY_FOR_HELP.match(text.strip()))


LABEL = "SIMULATED 911 (demo sandbox: no real call, text or number is dialed)"
PERSONA_ADDRESS = "12 Elm Street (invented demo address)"


def respond(text: str, now: datetime.datetime | None = None) -> dict:
    now = now or datetime.datetime.now(datetime.timezone.utc)
    stamp = now.strftime("%H:%M:%S UTC")
    steps = [
        {"step": "call_placed", "simulated": True, "detail": "Simulated dispatcher answered"},
        {"step": "location_shared", "simulated": True, "detail": PERSONA_ADDRESS},
        {"step": "caregiver_alerted", "simulated": True, "detail": "Sean would get an alert; nothing is sent in the demo"},
    ]
    response = (
        f"{LABEL}\n"
        f"[{stamp}] Calling 911 now. Stay on the line.\n"
        "Dispatcher (simulated): \"911, what is your emergency?\"\n"
        f"I told the dispatcher where you are ({PERSONA_ADDRESS}) and that you need help. "
        "I am alerting Sean (simulated). Stay where you are. If you can, unlock the door and sit or lie down "
        "somewhere safe until help arrives."
    )
    return {
        "response": response,
        "actions": [{"type": "emergency_call_simulated", "simulated": True, "dialed": None, "steps": steps}],
        "confidence": 1.0,
    }
