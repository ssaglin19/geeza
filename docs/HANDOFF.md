# Geeza - Project Handoff

Last updated: 2026-10-09. Replaces the 2026-09-22 Boosh handoff, which overclaimed. Open, owed and in-progress items only.

## What is built

- Python flow engine with unit tests (`engine/`), flow definitions (`flows/`).
- Hackathon web demo: Nemotron Nano 30B on Nebius Token Factory picks one tool per turn as JSON, code validates it, anything that acts needs YES. Fake vendor, no real money. Live at https://geeza.onrender.com (free Render, sleeps, about 50s cold start).
- `laya/`: training data and scripts from Sept 19-22. Not loaded by the demo.
- `docs/EVAL.md` (2026-10-09): measured scam screen on 40 synthetic messages against the live demo. Scams 20/20 flagged, legitimate 18/20 passed (two real-looking SSA and bank notices flagged). Small, hand-written set. Quote these numbers, not the old ones.
- Decision layer asks for a YES on 8 of 40 pasted messages (intent routing at medium confidence).

## Not verified or not built

- Scam screen and mail triage numbers in the old handoff (100% recall, 98.7% accuracy, "production-ready") have no eval in this repo. Do not quote them.
- Voice, iOS app and on-device (Bonsai, Laya, MLX) are spec only. The web demo is a stand-in, not the local version.
- Mac/Swift path is parked (decision 2026-10-05). Cloud Mac, Core ML, TestFlight and Apple Developer items from the old handoff are dropped.
- Code that exists only on Sean's own PC is not in this repo.

## Owed by Sean

- Fill the memory corpus (parents' routines, meds, contacts). Not started.
- Devpost demo video link (see `docs/DEVPOST.md`, currently TODO).

## Open

- GPU VMs: not covered. Credits are Token Factory only, $50 total (confirmed by Sean in the console 2026-10-06). Spend beyond that needs Sean's OK with the exact price.
- Cost-of-living flow: candidate pick is the electric bill spike explainer (idea 9 in `docs/COST-OF-LIVING-IDEAS.md`) on the Lakeshore Power demo bill. Waiting on Sean's OK on the pick before building. Fixtures stay synthetic.
- Durable memory: SQLite would not persist on Render free tier (disk is wiped on sleep or redeploy). Build locally with tests, or skip; do not claim persistence in the live demo.
- Known-sources list in the demo (Lakeshore Power, Patel Family Med, Ruth Miller) is invented. Waiting on Sean: keep for submission or supply a real list.
- Demo video: shot list is in `docs/DEMO-SCRIPT.md`. Sean records it and submits on Devpost by Oct 30 (posted to Slack #geeza 2026-10-09).
- Gap list (spec vs built) is finished and held.

## Read first when resuming

`README.md`, `docs/DECISIONS.md`, `docs/ARCHITECTURE.md`, `docs/CHANGES-SINCE-AUG-26.md`, `docs/DEVPOST.md`, `docs/EVAL.md`.
