# Clairic integration live check (2026-10-19)

Scope: the optional statement cross-check in the demo bill-pay offer step (`engine/boosh_flow/bill_extract.py`, `gateway/assistant.py`), run locally against the real Cloudflare Workers AI Clairic model. Synthetic Lakeshore Power statement text only, fake vendor, no payment, Nemotron replaced by the offline mock client. This was NOT run on the deployed site; the deployed demo does not call Clairic.

Calls: exactly 2 (hard cap 2), free plan, 434 + 438 input tokens (about 8 neurons at the listed price).

| Call | Input | Clairic output (value, confidence) | Result |
|---|---|---|---|
| 1, normal scenario via the pay flow | statement with "Previous balance $84.00 (paid)... Amount due $86.90" | vendor "Lakeshore Power" 0.989; amount_due 86.9 0.9998; due_date 2026-01-28 ~1.0 | matched the vendor page amount; the approval question was offered as before (still needs the person's YES) |
| 2, suspicious statement read directly | same text with "Amount due $412.00" | vendor "Lakeshore Power"; amount_due 412 0.9999; due_date 2026-01-28 | extracted correctly; the existing 15% amount check flagged it (390% from baseline) -> review |

What this shows: the integration reaches Clairic, parses the real response shape, and the checks behave on two easy cases. It is not an accuracy measurement. Error handling (nan/inf, wrong types, low confidence, look-alike payee, mismatch, reader down, parallel visitors) is covered only by offline tests with an injected client. Images are not supported. The 0.95 / 0.05 confidence thresholds remain experiment values.
