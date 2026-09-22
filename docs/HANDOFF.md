# Boosh — Project Handoff

Last updated: 2026-09-22 (evening session)

## Current State

**Repo:** 31 commits, 85 tests passing, clean working tree
**Architecture:** Text-first, phone-only, zero-infrastructure
**Positioning:** Technologically deficient users (not just elderly)

## What Works

| Component | Status | Notes |
|-----------|--------|-------|
| Scam screen | ✅ Laya, 100% recall, 0% FPR | Production-ready |
| Mail triage | ✅ Laya, 98.7% accuracy | Production-ready |
| Intent routing | ✅ Hybrid (keywords + fallback) | 3-class Laya blocked on Mac |
| Flow engine | ✅ 85 tests | 2 validated flows |
| 5 OpenMuse patterns | ✅ All working | Durable tasks, action review, PDF forms, goals, conversation |
| Memory corpus | ✅ Template + ingester | Waiting for content |
| Gateway server | ✅ Python/Flask | Shortcuts bridge ready |

## Blocked on Cloud Mac

| Task | Status | Notes |
|------|--------|-------|
| Swift build | ⏳ Ready | Package.swift fixed, workflow debugged |
| Core ML conversion | ⏳ Ready | Script written, needs macOS |
| 3-class Laya fine-tune | ⏳ Ready | Corpus ready, needs macOS |
| MLX/Bonsai integration | ⏳ Ready | Weights identified, needs macOS |
| TestFlight upload | ⏳ Ready | Needs Apple Developer account |

## Key Decisions

1. **Text-first, not app-first** — users text the bot like a person, no app to learn
2. **Phone-only, no server** — the phone is the server, SQLite is the database
3. **Technologically deficient, not elderly** — bigger market, same product
4. **Hybrid intent routing** — Laya for 3 classes, keywords for rest, LLM fallback
5. **Cloud Mac for validation** — rent first, buy later if MVP earns it

## Next Actions (Owner: Sean)

| # | Task | Priority | Notes |
|---|------|----------|-------|
| 1 | **Cloud Mac signup** | 🔴 Critical | MacinCloud recommended (~$50-100/mo) |
| 2 | **Apple Developer account** | 🔴 Critical | $99/yr, required for TestFlight |
| 3 | **Fill memory corpus** | 🟡 High | Parents' routines, meds, contacts |
| 4 | **Bonsai download** | 🟡 High | Run `scripts/download_bonsai.py` |
| 5 | **Parents' phone upgrade** | 🟢 Medium | 8GB minimum (iPhone 15 Pro/16) |

## Cloud Mac Recommendation

**MacinCloud** — cheapest entry, hourly billing, dedicated plans for persistent work.
- Plan: Cheapest dedicated Mac (not VM)
- Hardware: Apple Silicon (M1/M2)
- Storage: 256GB minimum
- Cost: ~$50-100/mo, cancel anytime

Alternative: **My Remote Mac** — $85/mo for M4, faster provisioning.

## Files to Read When Resuming

1. `docs/ARCHITECTURE.md` — System 0/1/2 design
2. `docs/TEXT-INTERFACE.md` — Text-first architecture spec
3. `docs/BUILD-SPEC.md` — Build pipeline and infrastructure
4. `docs/CLOUD-MAC.md` — Cloud Mac setup guide
5. `docs/EMERGENCY.md` — Emergency handling spec
6. `memory/corpus_template.md` — Memory corpus structure
7. `gateway/shortcut_bridge.md` — Shortcuts setup guide

## Open Items

- Emergency GitHub repo (Sean finding)
- GLiNER2 evaluation (blocked on Windows)
- Needle fine-tune (blocked on Windows)

## Contact

- Repo: https://github.com/ssaglin19/old-folks-app (private)
- Token: Expired — regenerate for pushes
