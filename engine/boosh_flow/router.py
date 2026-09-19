"""Confidence bands. Thresholds live in flow data, not in prompts."""
from __future__ import annotations

ACT = "act"
CONFIRM = "confirm"
ABORT = "abort"


def band(confidence: float, thresholds: dict | None = None) -> str:
    t = {"act": 0.85, "confirm": 0.5}
    if thresholds:
        t.update(thresholds)
    if confidence >= t["act"]:
        return ACT
    if confidence >= t["confirm"]:
        return CONFIRM
    return ABORT
