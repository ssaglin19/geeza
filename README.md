# Geeza

A personal AI companion for older adults. Geeza helps with everyday online chores: reading mail, spotting scams, and walking through routine tasks like paying a bill or refilling a prescription, in plain language and one step at a time.

Built for the Nebius x NVIDIA Global AI Hackathon, Personal AI track.

## Status

Early. This repo holds the design and the working pieces so far, not a finished app.

- `engine/` - deterministic flow engine in Python (stdlib only) with unit tests
- `flows/` - JSON definitions for task flows
- `laya/` - small classifier heads and synthetic training data for mail triage and scam screening
- `docs/` - scope, architecture and decisions
- `ios/` - planned iOS module map

All sample data in this repo is synthetic. The project started before the hackathon opened (originally named Boosh); the hackathon work adds the Nebius and NVIDIA layer.

## Nebius and NVIDIA

The assistant layer runs an NVIDIA open model (Nemotron) served from Nebius Token Factory. Work in progress is tracked in `docs/`.

## Run the engine tests

    python -m unittest discover -s engine

## License

MIT. See LICENSE.
