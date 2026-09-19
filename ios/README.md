# iOS app — module map

The native app. **Implementation is blocked on the Mac mini** (Xcode, Core ML
conversion, on-device debug). Everything else in this repo is buildable without
it; this file is the port contract so no time is wasted when the Mac arrives.

## Modules

| Module | Job | Ports from |
|---|---|---|
| `BooshApp` | SwiftUI shell: one screen, huge type, three buttons (Talk, Check my mail, Pay bills) | — |
| `VoiceIO` | Speech in via Apple on-device recognition; out via `AVSpeechSynthesizer` | — |
| `FlowRuntime` | Swift port of `engine/` — same flow JSON, same bands, same event stream | `engine/` (Python reference) |
| `BrowserShell` | `WKWebView` + JS bridge implementing the `Driver` protocol: snapshot elements, fill, click, read | `engine/boosh_flow/engine.py` `Driver` |
| `ApprovalGate` | The big button. Receives `APPROVAL_REQUIRED` events; nothing proceeds without a tap | `engine` `confirm` step |
| `LayaRuntime` | Core ML wrappers for the fine-tuned question packs; < 50 ms target | `laya/` |
| `LLMRuntime` | Bonsai ternary 8B via the PrismML **mlx-swift fork** (github.com/PrismML-Eng/mlx-swift); behind a tool-calling interface so the model is swappable | — |
| `MemoryStore` | SQLite FTS5 corpus (schema: handoff doc §6), caregiver-installed | handoff doc `ingest.py` |
| `Escalation` | Confirm-band and abort-band surfacing; caregiver notify via **draft** message (never auto-send) | `engine` events |
| `TraceLog` | Append-only local log of every event, tool call, prompt | `engine` event stream |

## Port contract for FlowRuntime

The Python reference engine is the spec. The Swift port must produce an
identical event stream for the same flow JSON + fixture snapshots. Port
`engine/tests/` to XCTest verbatim — including the phishing-lookalike test
(same DOM, attacker domain → `page_unrecognized`) and the fail-closed approval
tests (no approver → denied).

## Blocked-on-Mac checklist (in order)

1. Xcode project + `FlowRuntime` port + XCTest green
2. Core ML conversion of the fine-tuned Laya scam checkpoint (coremltools),
   latency measurement on device (< 50 ms gate)
3. MLX integration: ternary 8B on iPhone 16 Plus — measure tok/s, load time,
   thermals (gates: ≥ 5 tok/s sustained, load < 10 s, survives a 5-min session;
   else drop to ternary 4B and re-gate)
4. `BrowserShell`: WKWebView + JS element bridge against a real saved page
5. App shell + voice + approval UI, first live flow on a real vendor site

## Privacy rules for the app code

- No network except the WKWebView navigating to the flow's registered vendor
  URLs. No analytics, no crash reporting that ships content, no third-party SDKs.
- Credentials: Keychain, injected at runtime as `$credentials.*` — never in
  flow files, never logged.
- Trace log is local-only; exporting it is an explicit caregiver action.
- The model runtimes (MLX, Core ML) run in-process on device.
