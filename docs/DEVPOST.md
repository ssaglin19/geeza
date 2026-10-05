# Devpost text (draft)

**Project name:** Geeza
**Track:** Personal AI

## Tagline
A text assistant for older adults that reads their mail, spots scams, and never acts without a YES.

## Inspiration
Older parents get scam texts and emails that look real, and bills and reminders pile up. Most assistants are built to act fast. For this person, a wrong action costs money, so Geeza is built to ask first.

## What it does
You text Geeza in plain words. It can:
- read your mail back in simple language and warn you about scams without opening them
- check a pasted message for scams
- set a reminder
- write a note for a caregiver (saved as a draft, never sent)
- pay a bill (demo vendor, fake money), only after two YESes, and it stops on a suspicious amount

## How we built it
- NVIDIA Nemotron on Nebius Token Factory is the model (Nano 30B A3B in the live demo), behind an OpenAI-compatible client with an offline mock fallback.
- The model only proposes a tool call as JSON. Plain code validates it. Acting tools need the person's explicit YES. The model can raise a scam flag but cannot clear a rule-based one.
- A small Python gateway serves a web demo. The API key stays on the server.
- Deployed free on Render.

## Challenges
The live model first flagged a real utility bill as a scam. We fixed it with temperature 0, a 0.85 confidence bar for model-only flags, and code rules the model can't override.

## What's next
Voice, the on-device fast layer (Laya), and the other Nemotron models for a second opinion on scams.

## Links
- Demo: https://geeza.onrender.com (first load after idle can take about a minute)
- Code: https://github.com/ssaglin19/geeza
- Demo video: TODO
