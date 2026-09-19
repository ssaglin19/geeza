# Architecture

## The stack

```
┌───────────────────────────────────────────────────────────────┐
│ iOS app (SwiftUI)                                             │
│                                                               │
│  ┌─────────┐   ┌──────────┐   ┌────────────────────────────┐  │
│  │ VoiceIO │→→│ System 1 │→→│ System 0: FLOW ENGINE (code) │  │
│  │ spch in │   │ Laya     │   │  match → band → gate →      │  │
│  │ tts out │   │ CoreML   │   │  approve → execute         │  │
│  └─────────┘   └──────────┘   └──────────────┬─────────────┘  │
│       ↑             ↑                         │                │
│  ┌──────────────────────────┐   ┌────────────▼─────────────┐  │
│  │ System 2: Bonsai ternary │   │ BrowserShell: WKWebView  │  │
│  │ 8B (mlx-swift) — read,   │   │ in-app browser, app-owned│  │
│  │ explain, converse        │   │ cookie store, JS bridge  │  │
│  └──────────────────────────┘   └──────────────────────────┘  │
│                                                               │
│  ApprovalGate (big button) · Escalation (caregiver)           │
│  Memory (SQLite FTS5) · Trace log (every step, local)         │
└───────────────────────────────────────────────────────────────┘
```

## The three systems (Kahneman naming, deliberate)

| Layer | What | Implementation | Never does |
|---|---|---|---|
| **System 0 — execute** | Deterministic flow engine: page matching, step execution, gates, approval | Code. `engine/` (Python reference) → Swift port. Confidence = weighted anchor-match score | Ask a model what to do |
| **System 1 — decide** | Typed decisions on unstructured edges: intent routing, scam screen, mail triage, page-recognition assist | Laya fine-tuned per domain, Core ML, temperature-calibrated | Generate text; act on its own |
| **System 2 — comprehend** | Read mail/letters aloud, explain, converse, fill slots in flows | Bonsai ternary 8B via mlx-swift; Apple Foundation Models as complement | Navigate the browser; skip the gate |

## Walk-through: "pay the light bill"

1. **VoiceIO** transcribes on-device: "pay the light bill".
2. **System 1 (Laya)**: `choice` over the skill registry → `pay_bill` at 0.94.
   Band routing is code, not the model: ≥0.85 auto-select.
3. **Flow engine** loads `flows/consumers-energy-pay.json`, opens the
   in-app WKWebView at the entry URL.
4. **Page match** (code): weighted anchors on the login page → 1.0 → act band.
   Executes fill/fill/click. Credentials come from the keychain.
5. Dashboard: reads the amount (System 2 may be asked to read messy text if
   the selector misses), then the **amount-sanity gate**: within 15% of last
   month → pass. Not → abort + escalate.
6. Payment review page: match ≥0.85 → act. Then the step is `confirm`.
   **ApprovalGate**: the app freezes the flow and shows one button:
   "Pay $86.90 to Consumers Energy." No model output can skip this step —
   it is a step in the flow definition, mandatory for any flow with the
   `spends: true` flag.
7. Complete. Trace log records every event locally.

If at any point page confidence lands in the confirm band (0.5–0.85),
System 1 gets asked the page-guard question (`laya/questions/page-guard.json`)
as a second opinion before surfacing to the user; below 0.5, the flow aborts
and the caregiver escalation screen appears.

## Confidence bands

| Band | Range (default) | Behavior |
|---|---|---|
| act | ≥ 0.85 | proceed |
| confirm | 0.50–0.85 | second opinion → user confirms |
| abort | < 0.50 | stop, escalate to caregiver |

Thresholds are per-flow (`thresholds` in the flow JSON) and live in data,
not in prompts.

## What runs where

| Component | Runs on | Notes |
|---|---|---|
| Flow engine | phone | pure code |
| Laya (Core ML) | phone | 421M encoder, Neural Engine, target < 50 ms |
| Bonsai ternary 8B | phone | ~2.4 GB weights, mlx-swift fork |
| Flow definitions | phone, JSON | registered by caregiver setup |
| Memory corpus | phone, SQLite | caregiver-installed |
| Fine-tuning (Laya) | free Colab/Kaggle T4 | offline pipeline |
| Core ML conversion | Mac mini | one-time per checkpoint |
| App build | Mac mini | Xcode |

## Failure modes and their guards

| Failure | Guard |
|---|---|
| Site redesign breaks a flow | page match drops into confirm/abort; page-guard question; caregiver escalation |
| Confidently wrong small model | models never navigate; gates check amounts; approval gate is structural |
| Scam mail / phishing | System 1 scam screen on every message read |
| Half-completed payment | approval gate + trace log; flows are resumable |
| Thermal throttling on long sessions | bill-pay flows are short; comprehension requests are chunked |
