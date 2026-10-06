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
