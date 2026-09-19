# Decision log

Chronological record of the architecture decisions that shaped this build spec
(conversation of 2026-09-19 onward). Each entry replaces whatever the original
handoff doc said on the topic.

## D1 — Product: elderly-first assistant, not a personal assistant for the founder
The original spec was a private assistant for one technical user. The product is
now an extremely-easy-to-use assistant for elderly, routine-based users. First
user is the founder (guinea pig), then his parents.

## D2 — Deployment: phone-only, no home server
The original architecture had an always-on mini PC + brain box (Muse's cloud VM
replaced by owned hardware). Dropped: a per-household $600–800 box kills scale.
The app is the entire system.

## D3 — Minimum device: 8 GB Apple Intelligence-class iPhone
iPhone 15 Pro / 16 / 16 Plus or newer (parents will upgrade). This carries two
consequences: the Bonsai ternary 8B tier fits, and Apple's on-device Foundation
Models API is available as a System 2 complement.

## D4 — Browser tier: in-app WKWebView with deterministic registered flows
No app can drive Safari, but an app can drive its own WKWebView. No open-ended
agentic browsing — small models fumble it. Vendors are registered once; each has
a templated flow (login → find amount → sanity gate → approval gate → pay).
The model's job inside a flow is slot-filling and reading, never navigation.
Site logins live in the app's own cookie store.

## D5 — Execution confidence: code-computed, not model-claimed
Page match confidence = weighted anchor match score computed by code. Bands:
act ≥ 0.85, confirm 0.5–0.85 (surface to user), abort < 0.5 (escalate to
caregiver). Thresholds live in app code and flow definitions, auditable.

## D6 — System 1 decision layer: Laya (open weights), not Jev (hosted API)
TypeSafe's Jev pioneered the typed-decision pattern but is a hosted, waitlisted
API — sending the user's mail/bills to a third party violates principle 1.
Laya (Apache 2.0, 322–421M encoders, RLCD-trained, fine-tunable) runs locally.
Decision layer handles the unstructured edges: intent routing, scam screening,
mail triage, page-recognition assist. Must be fine-tuned per-domain and
temperature-calibrated (ships over-confident; ECE 0.466 until fitted).

## D7 — System 2 comprehension: PrismML Bonsai family ternary weights
Bonsai 2 27B (5.9GB) is the capability reference but does not fit any phone
(8.6GB pack on disk; no published iPhone numbers exist). Phone tier = ternary 8B
(~2.4GB) via the PrismML mlx-swift fork. The LLM is behind a stable tool-calling
interface so a better compressed model drops in when one ships (compression
frontier is moving fast — this is an explicit bet).

## D8 — Approval gate before anything that spends or sends
Structural, in code, not promptable around. A wrong step is equally wrong on a
routine Tuesday; routine-based users reduce task *space*, not failure *cost*.

## D9 — Caregiver escalation
Low confidence and broken flows stop and surface to a designated caregiver
(adult child). Elderly users cannot self-recover from a half-completed bill-pay;
silent failure is the enemy. The real failure mode is environment drift (site
redesigns), not model creativity.

## D10 — Memory: on-device SQLite
Chunked corpus schema (FTS5/BM25, headings, weights, pins) carried over from the
original spec §6 (`ingest/ingest.py`, tested). For elderly users the corpus is
routines, medication schedules, contacts, and family notes — installed by the
caregiver, not learned from the cloud.

## D11 — Voice-first interface
Elderly users don't type. Speech in via Apple's on-device speech recognition,
out via AVSpeechSynthesizer. The UI is one screen, a few large targets, and a
"watch it work" browser view.
