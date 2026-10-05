# Boosh

An on-device personal assistant for elderly users. One native iOS app; the model,
the decision layer, the browser automation, and the memory all live on the phone.
Nothing leaves the device except traffic to vendors the user already does business
with. No cloud model, no relay, no middleman.

**Status: spec + scaffold phase.** This repo supersedes `BOOSH — Project Handoff.txt`
(kept as history — it described the previous architecture: phone-as-client to a
home-server brain, which was dropped for scale reasons; see `docs/DECISIONS.md`).

## Principles (non-negotiable)

1. **Everything on-device.** Network only to the vendor being transacted with.
   No third-party API ever receives the user's content (mail, pages, voice).
2. **Code executes, models comprehend.** Deterministic flows do the acting;
   LLMs do the reading, listening, and explaining. Small models never drive
   open-ended browsing.
3. **The approval gate is structural.** Anything that spends or sends stops for
   a human tap. No model output can skip it.
4. **Low confidence escalates.** When a step is not confident, it stops and
   surfaces to the user or a caregiver. It never guesses forward.
5. **The model is a swappable component.** Same tool contract, same memory
   format, so a better on-device model drops in without a rewrite.

## Repo map

| Path | What it is | Needs Mac? |
|---|---|---|
| `docs/` | Scope, architecture, decision log | no |
| `engine/` | Flow engine — deterministic System 0 reference implementation (Python) with tests. Ported 1:1 to Swift for the app | no |
| `flows/` | Flow definitions (JSON): page matchers, steps, gates, thresholds | no |
| `laya/` | System 1 decision layer: typed question packs + fine-tuning/calibration plan | no (fine-tune runs on free Colab/Kaggle GPUs; Core ML *conversion* needs the Mac) |
| `ios/` | The app — module map; implementation blocked on Xcode/macOS | **yes** |
| `BOOSH — Project Handoff.txt` | Original 2026-09-19 spec (superseded, historical) | — |

## Target hardware

Minimum: 8 GB Apple Intelligence-class iPhone (iPhone 15 Pro / 16 / 16 Plus and up).
Development target device: iPhone 16 Plus. Fine-tuning: free Colab/Kaggle T4.
iOS build machine: used M1/M2 Mac mini.

## Running the reference engine tests

```
cd engine
python -m unittest discover -s tests -t . -v
```

Python 3.10+, stdlib only.
