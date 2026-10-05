# Geeza

A personal AI companion for older adults, built for the Nebius x NVIDIA Global AI Hackathon (Personal AI track).

The goal: help with everyday online chores such as reading mail, spotting scams, and walking through routine tasks like paying a bill or refilling a prescription, in plain language and one step at a time.

## Status: early

This repo is a design plus working building blocks. It is not a finished app and there is no live demo yet.

What exists today:

- `engine/` - deterministic flow engine in Python (stdlib only) with unit tests
- `flows/` - JSON definitions for task flows
- `laya/` - small classifier heads and synthetic training data for mail triage and scam screening
- `docs/` - scope, architecture and decisions
- `ios/` - planned iOS module map (no app code yet)

All sample data in this repo is synthetic. The project started before the hackathon opened (originally named Boosh).

## Hackathon plan (not built yet)

Planned work for the hackathon, in progress:

- Serve an NVIDIA open model (Nemotron) from Nebius Token Factory as the assistant layer
- Connect it to the flow engine so the model plans and the engine executes
- Ship a working demo

Nothing above is implemented yet. This section will change as it lands. The older design docs in `docs/` describe an on-device-only approach; the hackathon version adds a cloud model call, and the docs will be updated to match.

## Run the engine tests

    python -m unittest discover -s engine

## License

MIT. See LICENSE.
