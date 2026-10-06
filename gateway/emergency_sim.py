"""SIMULATED 911 dispatcher for the hackathon demo.

Nothing here can reach a real number: this module imports no network, phone or subprocess code,
and builds only a canned, clearly labelled transcript. The person sees that it is a simulation.
A real build would hand off to the phone's emergency call; that part is parked with the iOS work.
"""
from __future__ import annotations

import datetime

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
