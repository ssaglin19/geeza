"""Electric bill explainer: why did this bill change?

Plain code does all the arithmetic. The model, when live, only rewrites the finished facts
as a short plain-language explanation, and code rejects any reply that contains a number
that is not in the facts. Nothing here sends, pays, or changes anything. The billing-review
request is a draft text for a person to read.

Statements are dicts: period, days, kwh, rate (dollars per kWh), fixed (dollars),
extras (list of {"label", "amount"}). All demo data is synthetic.
"""
from __future__ import annotations

import re

SPIKE_PCT = 15.0   # same 15% bar as the bill-pay amount-sanity gate
SAFETY = ("Please do not turn off heat, cooling or medical equipment to save money. "
          "If a cheaper bill would mean going without, ask Sean or the utility first.")


def _c(x: float) -> float:
    return round(x + 1e-9, 2)


def total(s: dict) -> float:
    return _c(s["kwh"] * s["rate"] + s["fixed"] + sum(e["amount"] for e in s.get("extras", [])))


def analyze(history: list[dict], current: dict) -> dict:
    """Compare `current` with the average of `history`. Effects add up exactly to the change."""
    if not history:
        raise ValueError("need at least one earlier statement")
    n = len(history)
    b_kwh = sum(h["kwh"] for h in history) / n
    b_rate = sum(h["rate"] for h in history) / n
    b_fixed = sum(h["fixed"] for h in history) / n
    b_extras = sum(sum(e["amount"] for e in h.get("extras", [])) for h in history) / n
    b_total = b_kwh * b_rate + b_fixed + b_extras
    c_extras = sum(e["amount"] for e in current.get("extras", []))
    c_total = current["kwh"] * current["rate"] + current["fixed"] + c_extras
    effects = {
        "usage": (current["kwh"] - b_kwh) * b_rate,
        "rate": (current["rate"] - b_rate) * current["kwh"],
        "fixed": current["fixed"] - b_fixed,
        "extra charges": c_extras - b_extras,
    }
    delta = c_total - b_total
    pct = 100.0 * delta / b_total if b_total else 0.0
    ranked = sorted(effects.items(), key=lambda kv: abs(kv[1]), reverse=True)
    return {
        "period": current["period"], "months_compared": n,
        "bill": _c(c_total), "usual_bill": _c(b_total), "change": _c(delta), "change_pct": round(pct, 1),
        "kwh": current["kwh"], "usual_kwh": round(b_kwh),
        "rate": current["rate"], "usual_rate": round(b_rate, 4),
        "days": current["days"], "extras": [dict(e) for e in current.get("extras", [])],
        "effects": {k: _c(v) for k, v in effects.items()},
        "main_reason": ranked[0][0] if abs(ranked[0][1]) >= 0.005 else None,
        "spike": pct >= SPIKE_PCT,
    }


def _money(x: float) -> str:
    return f"${abs(x):,.2f}"


def template(a: dict) -> str:
    """Deterministic explanation written by code. Used as the fallback and as the safe default."""
    if not a["spike"] and a["change_pct"] < SPIKE_PCT:
        word = "about the same as" if abs(a["change_pct"]) < 5 else ("lower than" if a["change"] < 0 else "a bit higher than")
        return (f"Your {a['period']} bill is {_money(a['bill'])}, {word} your usual {_money(a['usual_bill'])} "
                f"(the average of your last {a['months_compared']} bills). Nothing looks unusual.")
    lines = [f"Your {a['period']} bill is {_money(a['bill'])}. Your usual is {_money(a['usual_bill'])}, "
             f"so it is {_money(a['change'])} higher ({abs(a['change_pct']):.0f}%)."]
    parts = []
    for k, v in sorted(a["effects"].items(), key=lambda kv: abs(kv[1]), reverse=True):
        if abs(v) >= 0.5:
            parts.append(f"{k}: {'+' if v > 0 else '-'}{_money(v)}")
    if parts:
        lines.append("Where the change comes from: " + "; ".join(parts) + ".")
    for e in a["extras"]:
        lines.append(f"The bill has a line called \"{e['label']}\" for {_money(e['amount'])}.")
    lines.append(f"You used {a['kwh']:,} kWh against a usual {a['usual_kwh']:,} kWh.")
    return " ".join(lines)


def next_steps(a: dict) -> list[str]:
    if not a["spike"]:
        return []
    steps = ["Ask Lakeshore Power for a billing review. I wrote a draft below; nothing is sent."]
    if a["extras"]:
        steps.append("Ask what the extra charge is for and whether it is correct.")
    steps.append("Ask whether any bill help or payment plan applies. I cannot say you qualify.")
    return steps


def draft_review_request(a: dict) -> str:
    extra = "".join(f" The bill includes \"{e['label']}\" for {_money(e['amount'])}." for e in a["extras"])
    return (f"Hello, I am asking for a billing review of my {a['period']} bill of {_money(a['bill'])}. "
            f"My usual bill is about {_money(a['usual_bill'])}.{extra} "
            "Please explain each charge, check whether the meter reading was actual or estimated, "
            "and tell me if any bill assistance or payment plan is available. Thank you.")


_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _norm(tok: str) -> str:
    t = tok.replace(",", "")
    return t[:-2] if t.endswith(".0") else t


def allowed_numbers(a: dict) -> set[str]:
    vals = [a["bill"], a["usual_bill"], abs(a["change"]), abs(a["change_pct"]), round(abs(a["change_pct"])),
            a["kwh"], a["usual_kwh"], a["rate"], a["usual_rate"], a["days"], a["months_compared"]]
    vals += [abs(v) for v in a["effects"].values()] + [e["amount"] for e in a["extras"]]
    out = set()
    for v in vals:
        for f in (f"{v}", f"{v:.2f}", f"{v:.1f}", f"{v:.0f}", f"{v:.4f}".rstrip("0")):
            out.add(_norm(f))
    out.update({"1", "2", "3"})
    return out


def numbers_ok(text: str, a: dict) -> bool:
    ok = allowed_numbers(a)
    return all(_norm(t) in ok for t in _NUM.findall(text))


EXPLAIN_SYSTEM = ("You explain an electric bill to an older adult in plain words. Use only the facts given. "
                  "Do not invent causes, do not promise savings, do not tell them to use less heat or cooling. "
                  "Use at most 4 short sentences. Do not use any number that is not in the facts.")


def explain(a: dict, client=None) -> dict:
    """Return {"text", "source"}. The model only words the facts; code checks its numbers."""
    base = template(a)
    if client is None or not getattr(client, "live", False) or not a["spike"]:
        return {"text": base, "source": "code"}
    import json
    try:
        raw = client.complete([{"role": "system", "content": EXPLAIN_SYSTEM},
                               {"role": "user", "content": "Facts:\n" + json.dumps(a)}], max_tokens=300)
    except Exception:
        return {"text": base, "source": "code"}
    raw = (raw or "").strip()
    if getattr(client, "used_fallback", False) or not raw or raw.startswith(("{", "[")) or not numbers_ok(raw, a):
        return {"text": base, "source": "code"}
    return {"text": raw, "source": "model"}
