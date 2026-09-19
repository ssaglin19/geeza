"""Deterministic gates: money and safety checks in code, never in prompts."""
from __future__ import annotations


def _parse_amount(value) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace("$", "").replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def amount_sanity(value, last, within_pct: float) -> tuple[bool, str]:
    v, l = _parse_amount(value), _parse_amount(last)
    if v is None or l is None:
        return False, f"unparseable amount: {value!r} vs baseline {last!r}"
    if l <= 0:
        return False, "no usable baseline amount"
    delta = abs(v - l) / l * 100.0
    if delta <= within_pct:
        return True, f"{v:.2f} within {within_pct:.0f}% of baseline {l:.2f}"
    return False, f"{v:.2f} deviates {delta:.0f}% from baseline {l:.2f}"


def ctx_get(ctx: dict, dotted: str):
    """Walk a dotted path like 'history.vendor_last' through nested dicts."""
    cur = ctx
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def evaluate_gate(params: dict, ctx: dict) -> tuple[bool, str]:
    gtype = params.get("type")
    if gtype == "amount_sanity":
        value = ctx_get(ctx, params["value_key"])
        last = ctx_get(ctx, params["last_key"])
        return amount_sanity(value, last, params.get("within_pct", 15.0))
    return False, f"unknown gate type: {gtype!r}"
