# Build Spec — Boosh v1

## Overview

Text-first personal assistant for elderly users. No app to learn — they text,
the bot responds. Gateway runs on their phone (Shortcuts bridge) or a home
server (Mac mini / cloud Mac for dev).

## Architecture

```
User (iPhone) ──text──► Shortcuts ──► Gateway (local server)
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │  System 1: Laya     │  Intent routing, scam
                              │  (Core ML, on-device)│  screen, mail triage
                              └─────────────────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │  System 0: Flow     │  Deterministic execution
                              │  Engine (Swift)     │  WKWebView, approval gate
                              └─────────────────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │  System 2: Bonsai   │  Comprehension, conversation
                              │  (MLX, on-device)   │  Reading, explaining
                              └─────────────────────┘
```

## Components

| Component | Language | Location | Status |
|-----------|----------|----------|--------|
| Gateway server | Python | `gateway/server.py` | ✅ Built, tested |
| Shortcut bridge | Apple Shortcuts | `gateway/shortcut_bridge.md` | ✅ Spec'd |
| Flow engine | Python → Swift | `engine/` | ✅ Python, 85 tests |
| Intent router | Python → Swift | `engine/boosh_flow/intent_router_hybrid.py` | ✅ Hybrid built |
| Scam screen | Laya (Core ML) | `laya/` | ✅ Fine-tuned, 100% recall |
| Mail triage | Laya (Core ML) | `laya/` | ✅ Fine-tuned, 98.7% |
| Bonsai runtime | MLX Swift | `ios/` | ⏳ Blocked on Mac |
| iOS app shell | SwiftUI | `ios/` | ⏳ Blocked on Mac |
| Memory corpus | Markdown | `memory/` | ✅ Template ready |

## Build Pipeline

### Phase 1: Local Development (Current)

- Python reference implementation
- 85 tests passing
- Flow definitions validated
- Laya models fine-tuned
- Gateway server running locally

### Phase 2: Cloud Mac CI (Next)

- GitHub Actions macOS runner
- Swift package build + test
- Fastlane for TestFlight upload
- Automated on every push to `main`

### Phase 3: Device Testing (TestFlight)

- Deploy to Sean's iPhone 16 Plus
- Real-world usage testing
- Thermal, battery, memory profiling
- Iterate on UX

### Phase 4: Parent Deployment

- Parents' phones (upgraded to 8GB minimum)
- TestFlight or App Store
- Caregiver (Sean) manages corpus and flows

## Infrastructure

| Resource | Purpose | Cost |
|----------|---------|------|
| GitHub Actions macOS | CI/CD | Free (2,000 min/mo) |
| Apple Developer Account | TestFlight, App Store | $99/yr |
| MacStadium / MacWeb | Interactive dev (optional) | $30-100/mo |
| iPhone 16 Plus | Guinea pig device | Already owned |
| Parents' iPhones | Target devices | TBD (upgrade needed) |

## Security Model

- No cloud APIs for user data (**hackathon build:** System 2 calls Nemotron on Nebius Token Factory, see D12)
- All inference on-device (**hackathon build:** System 2 only; the flow engine and gates stay local code)
- Credentials in iOS Keychain
- Approval gate for financial actions
- Caregiver escalation for failures
- Group chat detection (privacy)

## Success Metrics

| Metric | Target | How measured |
|--------|--------|------------|
| Scam screen recall | ≥ 0.95 | Laya eval harness |
| Mail triage accuracy | ≥ 0.95 | Laya eval harness |
| Intent routing accuracy | ≥ 0.80 | Hybrid router tests |
| Flow completion rate | ≥ 0.90 | Trace logs |
| User (parent) task success | ≥ 0.80 | Weekly check-ins |
| Battery impact | < 5% per hour | iOS battery stats |
| Thermal throttling | None in 5-min session | Xcode Instruments |

## Risks

| Risk | Mitigation |
|------|------------|
| Shortcuts bridge unreliable | Fallback: Apple Business Chat or app install |
| Laya intent routing too weak | Hybrid with keyword fallback (already built) |
| Bonsai too slow on iPhone | Drop to 4B tier, or use Apple Foundation Models |
| Parents won't use it | Text interface is zero-learning; start with weather/scores |
| Site redesign breaks flows | Control scorer + page-guard + caregiver alert |

## Open Questions

1. Does Shortcuts automation work reliably for text forwarding?
2. Can we get Apple Business Chat approved?
3. What's the real Bonsai performance on iPhone 16 Plus?
4. How do we handle iOS app updates without breaking flows?
