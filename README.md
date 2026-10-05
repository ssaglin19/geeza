# Geeza

A personal AI companion for older adults, built for the Nebius x NVIDIA Global AI Hackathon (Personal AI track).

The goal: help with everyday online chores such as reading mail, spotting scams, and walking through routine tasks like paying a bill or refilling a prescription, in plain language and one step at a time.

## Status: early

This repo is a design plus working building blocks. It is not a finished app.

What exists today:

- `engine/` - deterministic flow engine in Python (stdlib only) with unit tests
- `flows/` - JSON definitions for task flows
- `laya/` - small classifier heads and synthetic training data for mail triage and scam screening
- `docs/` - scope, architecture and decisions
- `ios/` - planned iOS module map (no app code yet)

All sample data in this repo is synthetic. The project started before the hackathon opened (originally named Boosh).

## Hackathon build

System 2 (the model that reads, explains and chats) is NVIDIA Nemotron on Nebius Token Factory, behind an OpenAI-compatible client with an offline mock fallback (`engine/boosh_flow/nebius.py`). Decision record: `docs/DECISIONS.md` D12.

- Scam screen: keyword and sender-domain rules run first. The model can add a warning but cannot clear one. A flagged message is never read aloud.
- Mail read-back: the model explains clean mail in plain words.
- Bill pay: the real flow engine runs against a fake utility vendor (`flows/examples/demo-utility-pay.json`). The amount-sanity gate and the approval step are code. The model cannot skip them, and the person's YES only covers the amount they were shown.
- Interface: text-first. `gateway/server.py --demo` serves a chat page and the `/message` endpoint.

Status: the code and tests above are in this repo. Live calls to Nebius have not been verified yet and there is no hosted demo URL yet. This section will say so when that changes.

Run the demo locally (offline mock without a key):

    NEBIUS_API_KEY=... python gateway/server.py --demo --port 8080

The key is read from the environment only. All emails, vendors and amounts in the demo are fake.

## Run the engine tests

    cd engine && python -m unittest discover -s tests -t .

## License

MIT. See LICENSE.
