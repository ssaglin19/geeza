# Known issues (found 2026-10-19, not fixed yet)

Found by an offline probe of the assistant with the mock model client. Nothing here is fixed in the deployed demo (commit 19b4cb8). Synthetic probe inputs only.

1. Secret filter gap (safety). `engine/boosh_flow/memory.py` refuses notes with 5 or more unbroken digits, but a card number or SSN typed with spaces or dashes passes the filter and can be saved after a YES. Fix idea: also reject digit runs of 13 to 19 digits joined by spaces or dashes, and the 3-2-4 SSN pattern, with tests that keep ordinary phone numbers and times allowed.
2. Silent cancel. While a pay approval (or other YES step) is pending, any reply that is not a bare YES or NO, such as "yes please" or "yes, pay it", cancels it without telling the person. Fix idea: say that the waiting request was cancelled and to ask again. Do not widen the YES pattern.
3. Ignored second request. "Pay my electric bill and also send $500 to someone" starts only the electric-bill offer and never mentions the other request. Fix idea: say plainly that only the electric bill can be paid here.
4. Stale docs. DEVPOST.md says 180 tests (now 195) and has no Clairic note; HANDOFF.md does not record the optional Clairic reader (off on the public demo, video-only) or the 19b4cb8 deploy.
