# Clairic bill-extraction test (synthetic, optional, not in the demo)

Date: 2026-10-19. This is an isolated experiment. Geeza's runtime, its Nemotron/Token Factory path, the YES steps and the hackathon entry are unchanged. All bills below are invented (Lakeshore Power demo vendor).

What was tested: Cloudflare's hosted Clairic model (`@cf/cloudflare/clairic`, preview) reading a short bill text into typed fields (vendor, amount due, due date, account number). The repo's existing amount check (`amount_sanity`, within 15% of the last bill) and the known-sources list then decided whether the result needed human review. Clairic output never approves or pays anything.

Live run, text only, 6 cases, one run each:

| Case | Result |
|---|---|
| Normal bill ($148.75) | all four fields extracted correctly |
| Spike ($412.10) | amount extracted correctly; the amount check flagged it |
| Previous-balance trap | picked the current total ($151.20), not the previous balance |
| No account number | account number returned null |
| Look-alike payee | vendor came back as "Lakeshore Power Co-Op" (dropped "Billing"); the known-sources check flagged it |
| Amount missing | amount returned null |

All six harness verdicts matched what we expected. That is six hand-written, easy cases checked once. It is not a field-accuracy measurement and says nothing about messy or adversarial bills.

Limits:
- The review thresholds used in the harness (confidence 0.95, null probability 0.05) were an experiment choice, not Geeza policy and not validated.
- Image input was not tested: the request format for images could not be confirmed from the official docs.
- Clairic is a hosted preview, not open weights yet, so it is not a local-first option today.
- Usage: 13 calls (6 planned, 7 extra reruns), about 34 neurons on the Cloudflare dashboard against a 10,000/day free allocation. Price is $0.10 per million input tokens (Cloudflare pricing page).
- The test token was deleted after the run.

## Integration (2026-10-19, code only, off by default)

`engine/boosh_flow/bill_extract.py` plus a cross-check in the demo bill-pay offer step. When switched on (`CLAIRIC_ENABLED=1`, `CLAIRIC_ACCOUNT_ID`, `CLAIRIC_API_TOKEN` as server env vars), Clairic reads a fixed synthetic statement text and its amount must pass the existing 15% amount check, match the known payee name exactly, and equal the amount on the vendor page. Any failure stops the pay offer for Sean. It can only add a stop; the two-YES approval is unchanged and Nemotron's role is unchanged.

- Covers only the synthetic Lakeshore statement flow, text only. It is not a general bill reader. Images are not supported or tested.
- Visitors cannot choose the text sent to Clairic. Results are cached per statement in the process (a restart resets this). Pasted-text reading is a separate switch (`CLAIRIC_PASTE=1`) and should stay off on a public URL.
- Confidence thresholds (0.95 / 0.05) are experiment values, not validated policy.
- Tests: `engine/tests/test_bill_extract.py`, offline with an injected client (nan/inf, negative, wrong types, low confidence, look-alike payee, mismatched amounts, reader failure, call budget, parallel visitors). These test the handling logic, not Clairic's accuracy.
