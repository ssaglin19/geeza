# Geeza - Project Handoff

Last updated: 2026-10-06. Replaces the 2026-09-22 Boosh handoff, which overclaimed. Open, owed and in-progress items only.

## What is built

- Python flow engine with unit tests (`engine/`), flow definitions (`flows/`).
- Hackathon web demo: Nemotron Nano 30B on Nebius Token Factory picks one tool per turn as JSON, code validates it, anything that acts needs YES. Fake vendor, no real money. Live at https://geeza.onrender.com (free Render, sleeps, about 50s cold start).
- `laya/`: training data and scripts from Sept 19-22. Not loaded by the demo.

## Not verified or not built

- Scam screen and mail triage numbers in the old handoff (100% recall, 98.7% accuracy, "production-ready") have no eval in this repo. Do not quote them.
- Voice, iOS app and on-device (Bonsai, Laya, MLX) are spec only. The web demo is a stand-in, not the local version.
- Mac/Swift path is parked (decision 2026-10-05). Cloud Mac, Core ML, TestFlight and Apple Developer items from the old handoff are dropped.
- Code that exists only on Sean's own PC is not in this repo.

## Owed by Sean

- Fill the memory corpus (parents' routines, meds, contacts). Not started.
- Devpost demo video link (see `docs/DEVPOST.md`, currently TODO).

## Open

- Whether Nebius hackathon credits cover GPU VMs (unconfirmed; Token Factory only is confirmed).
- Gap list (spec vs built) is finished and held.

## Read first when resuming

`README.md`, `docs/DECISIONS.md`, `docs/ARCHITECTURE.md`, `docs/CHANGES-SINCE-AUG-26.md`, `docs/DEVPOST.md`.
