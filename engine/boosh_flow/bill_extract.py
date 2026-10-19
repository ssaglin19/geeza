"""Optional bill-text extraction with Cloudflare Clairic (hosted preview). Read only.

Clairic reads pasted bill TEXT into typed fields. Code then checks them. The result is a
PROPOSAL for a person to look at: it never approves, starts or pays anything. The existing
amount_sanity gate, the known-source list and the two-YES approval stay in charge.

Off unless CLAIRIC_ENABLED=1 plus CLAIRIC_ACCOUNT_ID and CLAIRIC_API_TOKEN are set. Any
failure (off, network, bad schema, low confidence, odd values) returns status "review".
Text only: image input is not supported because the image request format is unverified.
The confidence thresholds below are experiment values, not validated policy.
"""
from __future__ import annotations

import json
import math
import os
import re
import urllib.request

from .gates import amount_sanity

MODEL_PATH = "@cf/cloudflare/clairic"
MAX_TEXT = 4000
MIN_CONF, MAX_PNULL = 0.95, 0.05   # experiment-only, not validated policy
MAX_CALLS = int(os.environ.get("CLAIRIC_MAX_CALLS", "20"))  # per process; Free plan is 10,000 neurons/day
FIELDS = {
    "vendor": {"type": "text", "instructions": "Name of the company that issued this bill"},
    "amount_due": {"type": "number", "decimals": 2, "unit": "USD",
                   "instructions": "Total amount due now for this billing period, not the previous balance"},
    "due_date": {"type": "date", "instructions": "Payment due date"},
}
REQUIRED = ("vendor", "amount_due", "due_date")
_calls = 0
_CACHE: dict[str, dict] = {}


def enabled() -> bool:
    return (os.environ.get("CLAIRIC_ENABLED") == "1" and bool(os.environ.get("CLAIRIC_ACCOUNT_ID"))
            and bool(os.environ.get("CLAIRIC_API_TOKEN")))


def http_call(body: dict) -> dict:
    url = ("https://api.cloudflare.com/client/v4/accounts/%s/ai/run/%s"
           % (os.environ["CLAIRIC_ACCOUNT_ID"], MODEL_PATH))
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
        "Authorization": "Bearer " + os.environ["CLAIRIC_API_TOKEN"], "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=30))
    if isinstance(r, dict) and r.get("success") is False:
        raise RuntimeError("clairic call failed")
    return r.get("result", r) if isinstance(r, dict) else {}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def _review(reasons, fields=None) -> dict:
    return {"status": "review", "reasons": reasons, "fields": fields or {}}


def paste_enabled() -> bool:
    """Reading arbitrary pasted text is a separate switch, off unless CLAIRIC_PASTE=1."""
    return enabled() and os.environ.get("CLAIRIC_PASTE") == "1"


def extract_cached(text, last_bill, known_sources, reference_date, call=None, within_pct=15.0) -> dict:
    """Same as extract, but one call per distinct text per process. For fixed server-side
    statements, so visitors cannot cause repeated calls."""
    if text not in _CACHE:
        _CACHE[text] = extract(text, last_bill, known_sources, reference_date, call, within_pct)
    return _CACHE[text]


def extract(text: str, last_bill: float, known_sources: list[str], reference_date: str,
            call=None, within_pct: float = 15.0) -> dict:
    """Return {"status": "ok"|"review", "reasons": [...], "fields": {...}}.
    "ok" means only: fields were read, are consistent, and passed the checks. A person still
    answers YES; the payment flow is untouched."""
    global _calls
    if call is None:
        if not enabled():
            return _review(["bill reading is not switched on"])
        call = http_call
    if not isinstance(text, str) or not text.strip():
        return _review(["no bill text"])
    if len(text) > MAX_TEXT:
        return _review(["bill text too long to read safely"])
    if _calls >= MAX_CALLS:
        return _review(["bill reading call limit reached"])
    _calls += 1
    body = {"state": text, "fields": FIELDS, "reference_date": reference_date}
    try:
        resp = call(body)
        answers = resp["answers"]
        assert isinstance(answers, dict)
    except Exception:
        return _review(["bill reader unavailable or returned an unexpected format"])

    why, out = [], {}
    for k in REQUIRED:
        a = answers.get(k)
        if not isinstance(a, dict):
            why.append(f"{k}: missing from reader output")
            continue
        v, conf, pn = a.get("value"), a.get("confidence"), a.get("p_null")
        if v is None:
            why.append(f"{k}: not found")
            continue
        if not all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
                   for x in (conf, pn)):
            why.append(f"{k}: bad confidence values")
            continue
        if conf < MIN_CONF or pn > MAX_PNULL:
            why.append(f"{k}: reader not sure")
        out[k] = v
    amt = out.get("amount_due")
    if amt is not None:
        if isinstance(amt, bool) or not isinstance(amt, (int, float)) or not math.isfinite(amt) or amt <= 0:
            why.append("amount_due: not a usable positive number")
            out.pop("amount_due")
        else:
            ok, msg = amount_sanity(amt, last_bill, within_pct)
            if not ok:
                why.append("amount check: " + msg)
    ven = out.get("vendor")
    if ven is not None:
        if not isinstance(ven, str) or _norm(ven) not in {_norm(s) for s in known_sources}:
            why.append("payee is not on the known list")
            out.pop("vendor", None)
    if "due_date" in out and not (isinstance(out["due_date"], str)
                                  and re.fullmatch(r"\d{4}-\d{2}-\d{2}", out["due_date"])):
        why.append("due_date: unexpected format")
        out.pop("due_date")
    return {"status": "review" if why else "ok", "reasons": why, "fields": out}
