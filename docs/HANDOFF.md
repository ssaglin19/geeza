# Boosh Handoff — Current State

**Date:** 2026-09-20
**Session:** Morning continuation
**Repo:** https://github.com/ssaglin19/old-folks-app (private)
**Branch:** main
**Last commit:** 4c69dc6

---

## What Boosh is now

A **text-first personal assistant** for elderly, routine-based users. No app to learn — they text like they'd text a person. The assistant lives on their phone (iPhone 15 Pro / 16 / 16 Plus or newer), runs entirely on-device, and never sends their data anywhere except vendors they already use.

**Core insight:** They don't know another alternative exists. Text messaging is the interface they already understand.

---

## Architecture (three systems)

| System | Role | Implementation | Status |
|--------|------|---------------|--------|
| **System 0** | Execute | Deterministic flow engine + WKWebView | ✅ 85 tests passing |
| **System 1** | Decide | Laya (scam/mail) + hybrid intent router | ✅ Scam 100%, mail 98.7%, intent hybrid |
| **System 2** | Comprehend | Bonsai ternary 8B (or Apple FM) | ⏳ Blocked on Mac |

**Interface:** Text messages via Shortcuts bridge → local gateway → Boosh stack. No app download required for basic use.

---

## Key decisions (this session)

| Decision | Rationale |
|----------|-----------|
| **Text-first, not app-first** | Users won't download apps. Text is the interface they know. |
| **Shortcuts bridge for v1** | No Twilio cost, no Apple Business Chat wait. Local network only. |
| **Hybrid intent routing** | Laya failed (41%), Needle failed (38%). 3-class Laya + keywords + fallback. |
| **Emergency = Crisis Connect + JustInCase** | SOS broadcast + emergency toolkit + offline knowledge. |
| **Kroger flow validated** | Second flow proves schema generalizes. 7 tests passing. |
| **Needle fine-tune blocked** | Windows CLI crashes. Script ready for Linux/Mac. |

---

## Current state by component

| Component | Status | Notes |
|-----------|--------|-------|
| Flow engine | ✅ 85 tests | 2 flows (Consumers Energy, Kroger) |
| Scam screen | ✅ Laya, 100% recall, 0% FPR | Ready for Core ML |
| Mail triage | ✅ Laya, 98.7% accuracy | Ready for Core ML |
| Intent routing | ✅ Hybrid | Laya 3-class + keywords + fallback |
| Emergency spec | ✅ Documented | Crisis Connect + JustInCase patterns |
| Text interface | ✅ Spec + gateway | Shortcuts bridge, local server |
| Memory corpus | ✅ Template | Needs Sean to fill out |
| Bonsai eval | ✅ Harness ready | Needs Mac |
| iOS app | ⏳ Blocked | Needs Mac |

---

## Open items

| Item | Owner | Priority | Notes |
|------|-------|----------|-------|
| **Mac mini purchase** | Sean | 🔴 Critical | ~$300 used M1/M2. Unblocks iOS, MLX, Core ML, Bonsai. |
| **Parents' phone models** | Sean | High | Exact models (12/13/14?) for RAM tier. |
| **Memory corpus content** | Sean | High | Fill out template with parents' info. |
| **3-class Laya fine-tune** | Sean | Medium | Optional. Replaces keyword fallback. |
| **GLiNER2 evaluation** | — | Low | Page matching resilience. |
| **Bonsai GGUF download** | — | Low | Can download now, test on Mac. |

---

## Next actions (in order)

1. **Buy Mac mini** — used M1/M2, 16GB, ~$300. This is the critical path.
2. **Fill out memory corpus** — with parents, using template.
3. **Get parents' phone models** — Settings → General → About.
4. **Run 3-class Laya fine-tune** (optional) — `python finetune_local.py --corpus ../datasets/intent_corpus_v2.jsonl --num-classes 3`
5. **Download Bonsai weights** — `huggingface-cli download prism-ml/Ternary-Bonsai-8B-gguf`

---

## Files to read when resuming

| File | Purpose |
|------|---------|
| `docs/HANDOFF.md` | This file — current state |
| `docs/DECISIONS.md` | D1–D11, full decision log |
| `docs/ARCHITECTURE.md` | Three systems, walkthrough |
| `docs/SCOPE.md` | v1 in/out, milestones, gates |
| `docs/TEXT-INTERFACE.md` | Text-first architecture spec |
| `docs/EMERGENCY.md` | Emergency handling spec |
| `memory/corpus_template.md` | Memory corpus template |
| `gateway/server.py` | Shortcuts bridge server |
| `gateway/shortcut_bridge.md` | Shortcut setup guide |

---

## Working style

- Terse, no assumptions, blunt disagreement
- Don't make spend/scope/vendor calls for Sean
- Every claim verified against code or docs
- Test before committing
- Push after every commit

---

## Session history

| Date | Commits | Key work |
|------|---------|----------|
| 2026-09-19 | 10 | Scaffold, flow engine, Laya fine-tune, emergency spec |
| 2026-09-20 | 8 | Text interface, hybrid router, Kroger flow, corpus template |

**Total:** 18 commits, 85 tests passing, 3 working models, 2 validated flows.
