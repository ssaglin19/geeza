# Geeza - Project Handoff

Last updated: 2026-10-23. Replaces the 2026-09-22 Boosh handoff, which overclaimed. Open, owed and in-progress items only.

## Current submission readiness - October 27, 2026
This section supersedes historical video/status notes below.

- Deadline: Friday October 30, noon Central (10am Pacific), verified against the official rules.
- Devpost remains an unsubmitted draft, 2/5 steps. Story, build tags and demo/repo links saved; required public-or-unlisted video URL missing. Gallery images are optional in the current form.
- Final 126-second v5 video is complete; upload approved, destination channel and visibility not yet resolved. No video uploaded or entry submitted.
- Additional info is an unfinished questionnaire, not only declarations: technical model/platform feedback, subjective ratings, AI-tool disclosure, personal eligibility and learning answers still need completion/review. Technical response drafts prepared privately; no unsupported declarations saved.
- Current Token Factory balance, expiry and functional AI access through December 15 judging end remain unverified. Final live-model regression remains held until credit coverage is resolved. Current no-login web access is not proof of working AI coverage through judging.
- No rebuild is currently planned. Remaining critical path: resolve credits and final live tests, upload approved video to the selected channel, finish/review questionnaire and obtain final submission approval.

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

- Token Factory funding and cost (recorded 2026-10-18, NOT verified): the demo and tests call Nemotron Nano 30B A3B with the Token Factory API key Sean provisioned on 2026-10-05. Sean reported $25 of credits on Oct 5, then $50 on Oct 6, and said "use them" (phonemsg-01M49DDQQK1NTRHPV1F8P4JTS7). Calls made: the 40-message eval rerun on 2026-10-18 plus recording and test calls on 2026-10-17 (the Oct 9 eval earlier). Exact cost, remaining balance and overage settings are unknown: the console needs a login we do not have (no saved session; Google password was rejected earlier) and Token Factory has no documented balance or usage API (docs and Nebius feature requests checked 2026-10-18). Nebius docs say billing requires a bank card and that the card is charged automatically when the balance is negative at month start or a billing threshold is reached, so a card charge cannot be ruled out until Sean checks the console Usage and Transactions tabs. No spend beyond the credits is authorized. No further model calls until checked.
- GPU VMs: not covered. Credits are Token Factory only, $50 total (confirmed by Sean in the console 2026-10-06). Spend beyond that needs Sean's OK with the exact price.
- Cost-of-living flow built 2026-10-09: electric bill explainer (idea 9). `engine/boosh_flow/bill_explainer.py`, fixtures in `gateway/demo_data.py` (BILL_HISTORY, BILL_CURRENT), tool `explain_bill`, tests in `engine/tests/test_bill_explainer.py`. Ask "why is my electric bill so high?" (suspicious scenario shows the spike). Code computes; model only orders code-written fact sentences; code requires every sentence exactly once and rejects extra fields. Draft request is never sent. Deployed to Render (manual deploy of 6fda37f, 2026-10-10) and live-verified: the question routes to explain_bill, and pay_bill is unaffected. Spike UI verified live 2026-10-11 after session-isolation deploy. One Nemotron attempt returned offline fallback, before the live model fix described below.
- Session isolation built 2026-10-10: opaque HttpOnly browser cookies own approvals, notes, reminders, drafts and bill scenarios. Scenario changes clear only that visitor's pending action. Offline HTTP tests cover separate visitors, forged cookies, changed amounts, spike explanation and malformed payloads. Offline browser verification passed on desktop and 390px mobile: spike explanation and draft, blocked spike payment, separate normal scenario and two-YES payment. Actual pixels inspected. Merged PR #1 and deployed `373e8ea` to the existing free Render service on 2026-10-11 10:19 Central. Live checks: HttpOnly/SameSite cookie, independent scenarios, normal code-only explanation, and spike draft/safety text. Spike used deterministic fallback after one failed model call. No retry; later resolved as described below.
- Offline regression runner: `python scripts/test_demo.py` runs 199 tests (2026-10-19) without keys or model downloads. Optional GLiNER evaluation is excluded explicitly; running plain `unittest discover` shows one import error for `engine/tests/test_gliner_eval.py` because the optional `gliner` package is not installed. That error is expected and not a code failure. CI workflow is preserved in the patch only, not applied. Bill-average arithmetic now averages actual usage-times-rate, not the product of two averages.
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

## Update 2026-10-19

- Optional Clairic bill reader (`bill_extract.py`) is built and tested offline, and is dormant on Render: no Clairic env vars, off for public visitors, video-only. It can add a stop but never approves a payment; the amount gate, known-payee check and two-YES approval are unchanged. Recorded results: `docs/CLAIRIC-BILL-TEST.md`, `docs/CLAIRIC-INTEGRATION-LIVE-CHECK.md`.
- Three assistant edge cases fixed offline-tested on main (6b8104d plus the compound-route follow-up): spaced card/SSN digits in notes, silent cancel on a non-YES reply, and an ignored second money request (also on the model-confirmed route, covered with a mocked decider). Render was last deployed manually; verified for health only, not live behavior. Live model calls are on hold until Token Factory balance is checked.

## Update 2026-10-23

- Deadline re-verified on the official rules page: submission period ends Friday Oct 30, 2026, 10:00 am Pacific (noon Central). The Devpost draft page agrees ("7 more days to deadline" on Oct 23).
- Live app health checked: https://geeza.onrender.com/health returns ok after a cold start of about 22s. No model calls made.
- Devpost draft re-read (read-only, same GitHub OAuth sign-in): still DRAFT, 2/5 steps done (Manage team, Project overview). Project details are all still empty: About-the-project story, Built-with tags, Try-it-out links, image gallery, Demo video URL. Nothing edited or submitted. Entry text stays in `docs/DEVPOST.md` awaiting Sean's review.
- Token Factory balance: docs re-checked - still no documented balance or usage API (billing docs point to the console Usage tab; the balance-API feature request on Nebius's ideas portal is still open). Console sign-in is still blocked (Google passkey route; the earlier password attempt failed). The balance check stays with Sean and model calls stay on hold.
- Demo video: the loudness-normalized recut made 2026-10-18 was not recoverable through the tried routes. The 102.3s private review cut remains available privately to Sean. If he approves the cut, re-normalize its audio track or rebuild from `docs/DEMO-VIDEO-SCRIPT.md` before the public YouTube upload. Public upload and submission remain Sean's call.

## Update 2026-10-26

- Sean's "Work it" (10:25am CT) re-authorized continuation of the remaining finish work; spending, public video/submission and personal declarations stay gated.
- Devpost draft Project details filled and saved (draft only, nothing submitted): About-the-project story saved from this repo's `docs/DEVPOST.md` text; Built-with tags nvidia, nemotron, nebius, python, render; Try-it-out links https://geeza.onrender.com and the repo URL. Step counter still 2/5 because the required Demo video URL is empty. Additional info (submitter type, country of residence) and Submit untouched - those are Sean's personal declarations.
- Video assets: the Oct 18 loudness-normalized v3 recut is confirmed not surviving (main does not have it; the video worker agent is gone). Surviving sources are only the two Slack #geeza files: v2 review cut F0CA0KCNEK0 (102.3s) and the 24s Clairic insert F0CAF197CDC. Browser download is blocked: Slack magic-code sign-in hit an unsolved reCAPTCHA on two separate browser configs; no Slack password in the vault; the profile's Google account chooser only offers paul@paulcallsback.com (wrong identity for this workspace). No Slack file-download route exists in the Slack integration. Current unblock: Sean forwards both MP4s from #geeza; then join, loudness-normalize (v3 targets were -16.8 LUFS / -1.48 dBTP) and run final QC before any public upload.
- Token Factory balance still unverified; live model calls remain on hold; no calls made today. Live health 200 confirmed (~cold start).


## Update 2026-10-26 (later) - final cut v4 exists, pending Sean's review
- Both Slack MP4s recovered by main via Slack bot download (v2 cut + Clairic insert). Assembled final cut v4: 126.4s (2:06, under the 3:00 limit): v2 cut at the 63.0s narration pause, 24s silent Clairic insert, remainder; audio loudness-normalized to -17.0 LUFS / -1.5 dBTP (linear, v3 targets). QC done: full ASR transcript coherent end-to-end, both splice points frame-verified clean. v4 is private in slopline (handoff/geeza-demo-v4-126s.mp4), NOT committed here while pre-review.
- Sean's review of v4 gates the public YouTube upload; the video URL then goes into the Devpost draft (required field) before declarations/submit, all his calls.
- Devpost image-gallery upload blocked: AWS WAF cancels the XHR POST /software_photos (5 attempts, recorded). 5 gallery JPGs (3:2) are staged in slopline/handoff/gallery/. Retry later or Sean uploads them.

## Judge access + credits through judging (official rules, checked 2026-10-26)
- Official rules page: Judging Period Tuesday 2026-12-01 9:00am PT to Tuesday 2026-12-15 12:00pm PT; winners on or around 2027-01-11. The entrant must keep the project available "free of charge and without any restriction" for judges UNTIL THE JUDGING PERIOD ENDS (Dec 15). Judges are not required to test; video/text/images may be the basis.
- The public no-login demo URL (geeza.onrender.com) is a verified ACCESS MECHANISM only. It is not yet established as functional AI judging access through Dec 15.
- OPEN: (1) Token Factory balance (console-only read; no balance API exists); (2) credit expiry/coverage through the Dec 1-15 judging window; (3) live-model regression check (model calls on hold pending credits authority). If credits deplete or lapse, the app degrades to its code fallback wording, which is not equivalent to the AI build judges would be evaluating.
