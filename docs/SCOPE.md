# Scope — v1

## Users

- **Guinea pig:** the founder (iPhone 16 Plus, 128 GB). Tunes everything on his
  own phone before anyone else touches it.
- **Target:** his parents — elderly, routine-based, same tasks every day.
  Devices to be upgraded to the 8 GB minimum (D3).
- **Buyer persona (post-v1):** the adult child. The privacy claim ("nobody is
  in the middle") is the product.

## v1 in scope

1. **Voice chat.** Speech in (on-device recognition), speech out
   (AVSpeechSynthesizer). Bonsai ternary 8B. One screen, huge type.
2. **Reminders / medication prompts.** Local notifications. No network.
3. **Mail read-back + scam screen.** Read a message aloud (System 2); every
   message passes the Laya scam screen before anything else happens
   (`laya/questions/scam-screen.json`). Highest value-per-hour feature in v1.
4. **One registered browser flow, end to end.** Pay one real utility bill via
   in-app WKWebView: deterministic steps, amount-sanity gate, hard approval
   gate, trace log, caregiver escalation on failure.
5. **Caregiver escalation.** Low confidence → stop → surface. First version:
   on-screen; later: draft message to caregiver (compose draft only — never auto-send).

## v1 explicitly out of scope

- Open-ended browsing / "agent mode"
- Any purchase flow beyond the single registered vendor
- Background execution (nothing runs when the app is closed; iOS forbids it anyway)
- Android
- Any cloud model, API, or relay — including "just for tuning"
- Notifications that carry content off-device
- Multi-user / accounts

## v2 candidates (documented, not scheduled)

Patterns identified from WeKnora (Tencent) and other frameworks that would
improve UX but are not required for v1:

| Pattern | Source | What it does | Boosh application |
|---------|--------|--------------|-----------------|
| **Plan-Then-Execute decomposition** | WeKnora ReAct agent | Breaks multi-part queries into sequential sub-tasks | "Pay the bill and then call Sean" → `handle_bills` + `contact_family` in order |
| **Thread sessions / contextual stitching** | WeKnora IM quote-reply | Tracks pronouns across turns ("change that" → knows what "that" is) | "What time is my appointment?" → "Move it to 3pm" → resolves "it" |
| **Retrieval reranker** | WeKnora RAG pipeline | Filters noisy search results before answering | BM25 returns 8 chunks → reranker picks top 3, less prompt dilution |
| **Long-term memory** | WeKnora cross-session | Remembers user profile, preferences, frequent topics | "I take Lisinopril" → stored, recalled next session |
| **MCP tool protocol** | WeKnora Agent Skills | Standardized interface for external tools | If Boosh ever exposes tools to third-party agents |
| **Sandboxed execution** | WeKnora Docker/E2B | Isolated code execution environment | Not applicable — Boosh doesn't execute arbitrary code |

**Rationale for v2:** v1's single-shot intent routing handles the 80% case
("pay the light bill"). Multi-intent decomposition and pronoun resolution are
polish that significantly improve UX but don't block the core value proposition.

## Milestones

| # | Milestone | Blocked on |
|---|---|---|
| M0 | Repo scaffold: docs, flow engine reference + tests, question packs, flow schema | nothing — done in this commit |
| M1 | Laya v1 fine-tune: scam screen (public corpora + synthetic), temperature calibration, metrics report | nothing (Colab/Kaggle) |
| M2 | Flow registry + flow-authoring format frozen; 2 example flows validated against fixture pages | nothing |
| M3 | Swift port of the flow engine; runs under XCTest | **Mac** |
| M4 | MLX integration: ternary 8B on device — real tok/s + thermals on iPhone 16 Plus | **Mac** |
| M5 | App shell: voice in/out, one screen, approval gate UI | **Mac** |
| M6 | First real flow on a real vendor site, live | **Mac** |

## Measurement gates (spec-freeze criteria)

- Ternary 8B on iPhone 16 Plus: ≥ 5 tok/s sustained, load < 10 s, no thermal
  kill within a 5-minute session (if it fails: drop to ternary 4B and re-gate)
- Laya scam screen, fine-tuned + calibrated: recall ≥ 0.95 at precision ≥ 0.90
  in the act band; ECE ≤ 0.10 on held-out
- Laya Core ML on A18: < 50 ms per question pack
- Flow engine: 100% of reference tests green in both Python and Swift ports
