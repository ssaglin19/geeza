# What changed since Aug 26, 2026

Source: this repo's git history (`git log`). The first commit is 2026-09-19, so everything
in the repo was written after Aug 26. The project was called Boosh until the hackathon
build; it is Geeza now (same code).

## Sep 19 to Sep 22: the base (before the hackathon work)
- Deterministic flow engine, flow packs, scam-screen and intent-routing training pipelines.
- Mail read-back router, caregiver escalation path, emergency spec.
- Text-first gateway (Shortcuts bridge) and a Swift package port of the flow engine.
- Spec docs: SCOPE, BUILD-SPEC, ARCHITECTURE, DECISIONS (D1 to D11), TEXT-INTERFACE, HANDOFF.

## Oct 5: the hackathon build (Nebius x NVIDIA, Personal AI track)
- Repo made public under the MIT license, README written.
- `engine/boosh_flow/nebius.py`: OpenAI-compatible client for Nebius Token Factory
  (NVIDIA Nemotron), with an offline mock fallback.
- `engine/boosh_flow/assist.py`: scam screen (rules plus Nemotron) and mail read-back.
- `engine/boosh_flow/tools.py`: tool loop with five tools (read_mail, scam_check, pay_bill,
  set_reminder, tell_caregiver). The model only proposes JSON. Code validates it. Acting
  tools need the person's explicit YES. The caregiver note is a draft and is never sent.
- Scam rule: a code rule hit cannot be cleared by the model. A model-only flag needs
  confidence of at least 0.85 at temperature 0.
- Demo mode in the gateway (`python gateway/server.py --demo`): fake emails, fake vendor,
  no real money moves, 60 messages per hour per IP.
- Deployed on Render (free): https://geeza.onrender.com. The key is a server-side secret.
- Demo memory (D13): entry format borrowed from Agent Memory Repo, YES-gated writes, memory is data, invented seed data. Tools: recall_memory, remember, forget.
- Decision D12: the no-cloud principle is relaxed for the hackathon version only.

## Not changed / not done
- Voice-first (D11) is untouched. The demo is text-first (TEXT-INTERFACE.md).
- Laya is not loaded in the demo. Keyword rules stand in for the fast layer.
- Only Nemotron Nano is wired in. The web lookup tool is off.
- Code that exists only on the author's own machine is not in this repo.
## Oct 6 to Oct 10: live demo hardening and the first cost-of-living feature
- Typed decision layer (D14): the question packs in `laya/questions` (scam screen, mail triage, intent routing) are answered by one Nemotron Nano call each, and plain code applies the pack's confidence bands. The probabilities are the model's own, not calibrated; this is not Laya or Bonsai.
- SIMULATED 911 dispatcher flow (`gateway/emergency_sim.py`): a labelled sandbox transcript with an invented address; no call, text or number is ever dialed. Ordinary phrases like "can you help me pay my bill" do not trigger it; "check my mail" routes to mail.
- Known-sources payment rule: a payment request only warns when the sender is not on the caregiver's known-sources list (invented demo list: Lakeshore Power, Patel Family Med, Ruth Miller).
- Per-visitor session isolation: notes, approvals and scenario changes are not shared between demo visitors.
- README rewritten; Devpost draft added (`docs/DEVPOST.md`); demo redeployed live on Render 2026-10-06.
- `docs/COST-OF-LIVING-IDEAS.md` (Oct 8): nine cost-of-living ideas, paraphrased and labelled as ideas, not features.
- Electric bill explainer (Oct 9-10): "Why is my electric bill so high?" on the synthetic Lakeshore Power six-month history. Code does the math and names the biggest cause; the model only words it. A billing-review request is drafted, never sent. Live on Render 2026-10-10 with 14 passing tests.

## Oct 17 to Oct 19: eval rerun, edge-case fixes, optional Clairic reader
- Bug fixes found while recording the demo: the chat model looping its output after a pasted scam, the intent router refusing "Tell Sean I need groceries", and a bare YES with nothing pending. Each now has a regression test. Three more assistant edge cases fixed Oct 19: spaced card or SSN digits in a saved note, a non-YES reply cancelling a pending request without saying so, and a second money request being ignored. 199 offline tests in total as of 2026-10-19.
- Scam-screen eval rerun 2026-10-18 on the same 40 synthetic messages after the fixes: same result, 20 of 20 scams flagged, 18 of 20 legitimate passed (`docs/EVAL.md`).
- Optional Clairic bill reader (`engine/boosh_flow/bill_extract.py`): Cloudflare Workers AI Clairic extracts typed fields from pasted bill text ahead of Nemotron. It can only add a stop and never approves a payment. Off for public demo visitors; used in the demo video only. Tests and live-check notes: `docs/CLAIRIC-BILL-TEST.md`, `docs/CLAIRIC-INTEGRATION-LIVE-CHECK.md` (live check run locally against the real model, not on the deployed site).

## Open for submission (as of 2026-10-23)
- Demo video: a private review draft exists, not yet uploaded. The submission needs a public YouTube link.
- Devpost submission itself is pending. Deadline 2026-10-30 10:00 am PT.
- The Render demo and the Token Factory key must stay available to judges free of charge until the judging period ends (Dec 15, 2026).
