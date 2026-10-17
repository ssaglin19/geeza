# Geeza - Project Handoff

Last updated: 2026-10-11. Replaces the 2026-09-22 Boosh handoff, which overclaimed. Open, owed and in-progress items only.

## What is built

- Python flow engine with unit tests (`engine/`), flow definitions (`flows/`).
- Hackathon web demo: Nemotron Nano 30B on Nebius Token Factory picks one tool per turn as JSON, code validates it, anything that acts needs YES. Fake vendor, no real money. Live at https://geeza.onrender.com (free Render, sleeps, about 50s cold start).
- `laya/`: training data and scripts from Sept 19-22. Not loaded by the demo.
- `docs/EVAL.md` (2026-10-09): measured scam screen on 40 synthetic messages against the live demo. Scams 20/20 flagged, legitimate 18/20 passed (two real-looking SSA and bank notices flagged). Small, hand-written set. Quote these numbers, not the old ones.
- Decision layer asks for a YES on 8 of 40 pasted messages (intent routing at medium confidence).

## Not verified or not built

- Scam screen and mail triage numbers in the old handoff (100% recall, 98.7% accuracy, "production-ready") have no eval in this repo. Do not quote them.
- Voice, iOS app and on-device (Bonsai, Laya, MLX) are spec only. The web demo is a stand-in, not the local version.
- Mac/Swift path is parked (decision 2026-10-05). Cloud Mac, Core ML, TestFlight and Apple Developer items from the old handoff are dropped.
- Code that exists only on Sean's own PC is not in this repo.

## Owed by Sean

- Fill the memory corpus (parents' routines, meds, contacts). Not started.
- Final review/approval of the finished demo video and Devpost entry before the public YouTube upload and submit (video itself is agent-produced; link goes in `docs/DEVPOST.md`, currently TODO).

## Open

- GPU VMs: not covered. Credits are Token Factory only, $50 total (confirmed by Sean in the console 2026-10-06). Spend beyond that needs Sean's OK with the exact price.
- Cost-of-living flow built 2026-10-09: electric bill explainer (idea 9). `engine/boosh_flow/bill_explainer.py`, fixtures in `gateway/demo_data.py` (BILL_HISTORY, BILL_CURRENT), tool `explain_bill`, tests in `engine/tests/test_bill_explainer.py`. Ask "why is my electric bill so high?" (suspicious scenario shows the spike). Code computes; model only orders code-written fact sentences; code requires every sentence exactly once and rejects extra fields. Draft request is never sent. Deployed to Render (manual deploy of 6fda37f, 2026-10-10) and live-verified: the question routes to explain_bill, and pay_bill is unaffected. Spike UI verified live 2026-10-11 after session-isolation deploy. One Nemotron attempt returned offline fallback, before the live model fix described below.
- Session isolation built 2026-10-10: opaque HttpOnly browser cookies own approvals, notes, reminders, drafts and bill scenarios. Scenario changes clear only that visitor's pending action. Offline HTTP tests cover separate visitors, forged cookies, changed amounts, spike explanation and malformed payloads. Offline browser verification passed on desktop and 390px mobile: spike explanation and draft, blocked spike payment, separate normal scenario and two-YES payment. Actual pixels inspected. Merged PR #1 and deployed `373e8ea` to the existing free Render service on 2026-10-11 10:19 Central. Live checks: HttpOnly/SameSite cookie, independent scenarios, normal code-only explanation, and spike draft/safety text. Spike used deterministic fallback after one failed model call. No retry; later resolved as described below.
- Offline regression runner: `python scripts/test_demo.py` runs 180 tests without keys or model downloads. Optional GLiNER evaluation is excluded explicitly. CI workflow is preserved in the patch only, not applied. Bill-average arithmetic now averages actual usage-times-rate, not the product of two averages.
- Safe model diagnostics deployed 2026-10-11 at 10:23 Central, source `50a2657`, on existing Free Render. Exactly one spike request fell back with `ValueError`; no retries. Status/logs expose only the allowlisted exception class, never keys, headers or error bodies. Offline parsing hardening (`2b3cdb2`) validates envelope shapes, accepts one complete JSON/text fence, and preserves explicit fallback on empty/non-JSON envelopes. Non-JSON assistant prose remains valid for bill wording. Tests cover empty content, fences, malformed envelopes and non-disclosure. This was followed by the thinking-off and fact-boundary fixes below.
- Live model path verified 2026-10-11 at 10:47 Central, source `e467390`, deployed on existing Free Render. Documented `chat_template_kwargs.enable_thinking=false` avoids empty final content on short Nano requests. A live response then exposed an unsupported verbal claim that usage was unchanged, so the bill model role is now limited to ordering approved code-written fact sentences. Code rejects missing, duplicate or invented IDs and extra fields; it never displays new model claims. Two subsequent spike responses succeeded; captured response metadata confirms `wording=model`, `fallback=false`, Nano model ID, health `ok` and no exception. Correct output retains the $228.50 extra charge, $100.68 usage effect and 1,240 versus 510 kWh. Four verification calls in this pass; no further calls after success. Model card: https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16. Deploy: https://dashboard.render.com/web/srv-db22k817lnhs73dcogag/deploys/dep-db5qukfavr4c739ot610.
- Durable memory: SQLite would not persist on Render free tier (disk is wiped on sleep or redeploy). Build locally with tests, or skip; do not claim persistence in the live demo.
- Known-sources list in the demo (Lakeshore Power, Patel Family Med, Ruth Miller) stays synthetic for submission. These are invented demo fixtures, not verified real contacts. No decision is waiting on Sean.
- Live demo defects found 2026-10-17 and fixed (f13327f, deployed to the existing free Render service and verified live): looping chat output after a pasted scam and after a bare YES (reply guard in `assist.tame`, shorter chat prompt); "Tell Sean I need groceries" was refused by the intent router (code-first `TELL` match now runs before the router); a pasted message with scam signals now goes straight to scam_check; a bare YES/NO with nothing pending answers "There is nothing waiting for a YES right now." Tests: `engine/tests/test_demo_defects.py`, 180 offline tests total. Verified live: scam paste, note to Sean with YES, pills reminder with YES, simulated 911 (labeled, nothing sent), recall, mail, normal and suspicious pay, bill explainer.
- Demo video (updated 2026-10-17 2:15 PM Central): private narrated review draft, 102.3s, built from a fresh screen recording of the live app (each beat uses decisive recorded states held as stills, LLM wait trimmed, captions change per state, simulated labels visible). Narration is the generated WAV, re-timed per paragraph so outcome sentences land on the visible result. Fixes since the first cut: clean intro home view with the extended intro caption (Nemotron through Nebius, all-demo disclosure), no reload or idle footage, closing no longer claims every action needs YES (the emergency flow is a labeled simulation with no YES). Checks done: frame inspection at each outcome word onset and an ASR pass on the final track. NOT done: a human listen-through, loudness or tone check, so audio is not fully QC'd. Not published, not attached to Devpost. Script: `docs/DEMO-VIDEO-SCRIPT.md`. Sean reviews before any public upload or submission. Original user wording on record: Oct 6 "Finish GEEZA"; Oct 15 "When are they going to the ready for submitting"; Oct 17 "How much more work needs to be finished before you submit both hackathon items" and "You have all of the logins". None says outright to make the video, so the cut is a draft for his review. Entry text and submission remain unsubmitted (deadline Oct 30, noon Central).
- Gap list (spec vs built) is finished and held.

## Read first when resuming

`README.md`, `docs/DECISIONS.md`, `docs/ARCHITECTURE.md`, `docs/CHANGES-SINCE-AUG-26.md`, `docs/DEVPOST.md`, `docs/EVAL.md`, `engine/boosh_flow/bill_explainer.py`.

## Devpost access (verified 2026-10-17)

No standalone Devpost login in the vault. Sign in with "Log in with GitHub" using the saved GitHub ssaglin19 session in the cloud browser profile. It linked to Sean's existing Devpost account (email on file with Devpost, same as his Gmail) and opened the draft at https://devpost.com/software/geeza: status "Incomplete submission" for Nebius x NVIDIA Global AI Hackathon. Nothing edited or submitted. Do not create another Devpost account or change identity. Google sign-in is not the route (Sean uses a passkey).
