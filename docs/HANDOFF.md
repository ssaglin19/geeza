# Boosh — Project Handoff

**Date:** 2026-09-19 (evening)  
**Status:** M1 in progress, Mac mini is critical path  
**Repo:** https://github.com/ssaglin19/old-folks-app (private)

---

## What Boosh is

A private, local-first personal assistant for elderly users. Two jobs:

1. **Chat buddy / logic checker** — voice-first conversation, grounded in a pre-loaded corpus of routines, medications, contacts, family notes
2. **Personal assistant** — voice commands, mail read-back, bill pay, calendar, reminders — all on-device, no cloud, no middleman

**Non-negotiables:**
- The brain never leaves hardware the user owns
- Network only to vendors the user would talk to anyway (utility, pharmacy, etc.)
- Approval gate before any purchase or send
- One app, one interface — not a text-message bot

---

## Architecture (three systems)

| System | Role | Model | Status |
|--------|------|-------|--------|
| **System 0 — Execute** | Deterministic flows, code-defined confidence | None (code) | ✅ 67 tests passing |
| **System 1 — Decide** | Intent routing, scam screening, mail triage | Laya (421M) or Needle (29MB) | ⚠️ Mixed results |
| **System 2 — Comprehend** | Conversation, reading, explaining | Bonsai ternary 8B (2.4GB) | 📋 Ready for Mac |

**Key insight:** Code executes, model comprehends, logic decides when to stop.

---

## Current state

### ✅ Done and verified

| Component | Result | Notes |
|-----------|--------|-------|
| Flow engine (System 0) | 67 tests passing | Deterministic, fail-closed, approval gates |
| Scam screen | 100% recall, 0% FPR | Laya fine-tuned, 2/3 gates pass (ECE 0.203) |
| Mail triage | 98.7% accuracy | Laya fine-tuned, production-ready |
| Escalation path | 10 tests passing | Caregiver notification, user voice messages |
| Control scorer | 7 tests passing | GLiNER2-inspired, TF-IDF prototype |
| Bonsai eval harness | Ready | Mock runner validates gates, real MLX pending |
| CI smoke test | GitHub Actions | 100 examples, 1 epoch, passes on push |

### ⚠️ In progress / blocked

| Item | Status | Blocker |
|------|--------|---------|
| Intent routing | Laya 41%, Needle 57% | Needle fine-tune or accept Laya + keywords |
| Emergency handling | Basic keyword matching | **Sean to supply emergency GitHub repo** |
| GLiNER2 eval | Prototype only | Time — could run locally |
| Second example flow | Only Consumers Energy | Pick second vendor |
| Memory corpus | Schema only | Sean to provide parents' routines/meds/contacts |

### 📋 Ready for Mac mini

| Task | Depends on |
|------|-----------|
| Swift port of flow engine | Mac, Xcode |
| MLX integration (Bonsai 8B) | Mac, iPhone 16 Plus |
| Core ML conversion (Laya) | Mac |
| Cua Driver eval | Mac |
| Native app automation (Calendar, Mail, Contacts) | Mac, Cua Driver |

---

## Key decisions (D1–D11)

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Elderly-first product, not founder's assistant | Scale requires it |
| D2 | Phone-only, no home server | $800/box kills scale |
| D3 | Minimum: iPhone 15 Pro / 16 / 16 Plus (8GB) | Bonsai 8B fits, Apple Intelligence available |
| D4 | In-app WKWebView, deterministic flows | Can't drive Safari; small models fumble open browsing |
| D5 | Code-computed confidence, not model-claimed | Auditable, testable, no hallucination surface |
| D6 | Laya (open weights), not Jev (hosted API) | Privacy: no third party in the middle |
| D7 | Bonsai ternary for comprehension | 27B-class quality at 8B-class footprint |
| D8 | Approval gate before spend/send | Structural, in code, not promptable around |
| D9 | Caregiver escalation on low confidence | Elderly users can't self-recover |
| D10 | On-device SQLite memory | Chunked corpus, FTS5/BM25, caregiver-installed |
| D11 | Voice-first interface | Elderly users don't type |

---

## Dependencies

### Python packages (`requirements.txt`)
- `torch==2.5.1` (CPU)
- `laya==0.3.3`
- `scikit-learn==1.9.1`
- `cactus-needle==3.0.2` (evaluating)

### Model weights (Hugging Face)
- `convaiinnovations/laya` (421M) — System 1 base
- `prism-ml/Ternary-Bonsai-2-27B-mlx-2bit` (8.6GB) — Mac only
- `prism-ml/Ternary-Bonsai-8B-gguf` (~2.4GB) — iPhone 16 Plus
- `prism-ml/Ternary-Bonsai-4B-gguf` (~1.2GB) — parents' phones
- `Cactus-Compute/needle3` (8-29MB) — evaluating for intent routing

### External tools
- PrismML mlx-swift fork — Bonsai inference on iOS
- Cua Driver — native app automation (macOS)
- GitHub Actions — CI smoke tests

---

## Open items (Sean)

| Item | Priority | Notes |
|------|----------|-------|
| Emergency GitHub repo | 🔴 High | Small framework, may replace emergency handling |
| Parents' phone models | 🔴 High | Exact models (12/13/14) determine 4B vs 1.7B tier |
| Parents' memory corpus | 🟡 Medium | Routines, medications, contacts, family notes |
| Second vendor for flow | 🟡 Medium | Grocery or pharmacy |
| Mac mini purchase | 🔴 High | Used M1/M2 (~$300) or new M4 (~$600) |

---

## Next actions (in order)

1. **Sean:** Find and supply emergency GitHub repo
2. **Sean:** Run Needle fine-tune or accept Laya + keyword fallback for intent routing
3. **Sean:** Provide parents' exact phone models
4. **Sean:** Purchase Mac mini
5. **Agent:** Evaluate emergency repo, integrate if suitable
6. **Agent:** Write Needle fine-tune script (if pursuing)
7. **Agent:** GLiNER2 full eval (local)
8. **Agent:** Second example flow (when vendor chosen)

---

## Files to know

| File | Purpose |
|------|---------|
| `docs/DECISIONS.md` | D1–D11, dependencies, model weights |
| `docs/SCOPE.md` | v1 scope, milestones, measurement gates, OPEN ITEMS |
| `docs/ARCHITECTURE.md` | Three systems, walk-through, failure guards |
| `engine/boosh_flow/` | System 0 reference implementation (Python) |
| `engine/tests/` | 67 tests, all passing |
| `flows/` | Flow schema, authoring rules, example |
| `laya/` | Question packs, corpus generators, fine-tune scripts |
| `ios/README.md` | Module map, port contract, blocked-on-Mac checklist |

---

## Contact

- **Repo:** https://github.com/ssaglin19/old-folks-app (private)
- **Owner:** Sean (ssaglin19)
- **Agent session:** This conversation (Haze Code, 2026-09-19)

---

*This handoff supersedes the original `BOOSH — Project Handoff.txt` (2026-09-12). All source code is in the repo; nothing else is needed.*
