# Decision log

Chronological record of the architecture decisions that shaped this build spec
(conversation of 2026-09-19 onward). Each entry replaces whatever the original
handoff doc said on the topic.

## Dependencies

| Package | Version | Purpose | Source |
|---------|---------|---------|--------|
| `torch` | 2.5.1+cpu | ML runtime | PyPI |
| `laya` | 0.3.3 | System 1 decision engine (scam screen, intent routing, mail triage) | PyPI |
| `scikit-learn` | 1.9.1 | Metrics (ECE, calibration) | PyPI |
| `cactus-needle` | TBD | Tool calling, structured extraction, embeddings (evaluating) | PyPI |
| `gliner` | TBD | Control scoring (evaluating) | PyPI |
| `transformers` | 5.17.0 | Model loading (via laya) | PyPI |

## Model weights

| Model | Size | Purpose | Source |
|-------|------|---------|--------|
| `convaiinnovations/laya` | 421M | Base checkpoint for fine-tuning | Hugging Face |
| `prism-ml/Ternary-Bonsai-2-27B-mlx-2bit` | 8.6GB | System 2 comprehension (Mac only) | Hugging Face |
| `prism-ml/Ternary-Bonsai-8B-gguf` | ~2.4GB | System 2 comprehension (iPhone 16 Plus) | Hugging Face |
| `prism-ml/Ternary-Bonsai-4B-gguf` | ~1.2GB | System 2 comprehension (parents' phones) | Hugging Face |
| `Cactus-Compute/needle3` | 8-29MB | Tool calling, extraction, embeddings (evaluating) | Hugging Face |
| `fastino/gliner2-multi-v1` | TBD | Control scoring (evaluating) | Hugging Face |

## External tools

| Tool | Purpose | When |
|------|---------|------|
| Cua Driver | Native app automation (macOS) | Mac mini arrives |
| PrismML mlx-swift fork | Bonsai inference on iOS | Mac mini arrives |
| GitHub Actions | CI smoke tests | Already configured |

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

## D12 — Hackathon build: System 2 on Nebius Token Factory (2026-10-05)
For the Nebius x NVIDIA Global AI Hackathon (Personal AI track), the project owner chose to
switch from the earlier design wherever it conflicts with the hackathon scope. Changes:

- **System 2 (comprehend)** is NVIDIA Nemotron served by Nebius Token Factory
  (OpenAI-compatible API, `engine/boosh_flow/nebius.py`) instead of on-device Bonsai. D7 already
  put the LLM behind a stable interface so a model can be swapped; this is that swap.
- This overrides principle 1 ("no cloud model") for the hackathon version only. The deterministic
  parts are unchanged and still local code: flow engine, amount-sanity gate, approval gate (D8).
- The model never moves money. A scam warning from the code rules cannot be cleared by the model.
- No key means offline mock output, labeled as such. The key is read from `NEBIUS_API_KEY` and is never in the repo.
- The text-first gateway (`gateway/`) is the interface (TEXT-INTERFACE.md). Voice-first (D11) is not part of this build.
- Laya stays the planned on-device System 1. Until it is loaded here, `engine/boosh_flow/assist.py`
  stands in with keyword rules plus a model check.

## D13 — Hackathon demo memory in the Agent Memory Repo entry format (2026-10-05)
Keeps D10 (on-device store, caregiver-installed seed facts). Adopts only the entry format from
https://github.com/AgentMemoryRepo/agentmemoryrepo: a short `MEMORY.md` index, one-line facts
with `[source: ...; added: date]`, `[[links]]` to topic files. Not adopted: git repo per user,
the "dreaming" cleanup agent, shared or multiplayer memory, writes with no human in the loop.
Rules: memory is data, never instructions (entries are only shown or put in a labelled data
block, never parsed as tool calls); writes and removals come only from the person's own message
and need YES; no passwords, codes or long numbers; seed notes are read-only, the person can only
remove notes she saved herself. The demo seed (`memory/demo-memory/`) is invented data, and notes
saved in the live demo live in server RAM and vanish on sleep or restart.

## D14 - System 1 decision layer (question packs on Nemotron)

The question packs in `laya/questions/` (scam-screen, mail-triage, intent-routing) now run in the demo through `engine/boosh_flow/decider.py`. One Nemotron Nano call on Token Factory answers a whole pack (temperature 0, JSON only, the state is marked as untrusted data). Code validates the shape, normalizes, and applies the pack's own bands. Bad output or a mock fallback returns ok=False and the earlier behavior runs.

- Probabilities are self-reported by the model and not calibrated. This is not Laya, Bonsai or a trained decision model. The Laya encoder is not in the hosted demo.
- The model can raise a scam warning, never clear a code rule hit.
- Intent routing runs before tool choice: high >= 0.80 goes on, 0.50 to 0.79 asks "Did you want to...? YES", low goes to the normal path. Emergency prints an honest notice (the demo cannot call or text). Memory commands stay code-first.
- OPEN QUESTION for Sean: scam-screen.json says `requests_payment` >= 0.5 also triggers the warning. Read literally, that flags a real electric bill. The demo requires is_phishing >= 0.5 as well. The literal rule is computed and shown in the policy output, and a test pins the difference.
- Cost: about one extra call per email in read-back, and one per message for routing.
