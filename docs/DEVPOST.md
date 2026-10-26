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
- remember things you ask it to (it shows the note and where it came from, and saves only after YES) and forget them on request
- run a simulated 911 call when you say you fell or need help (a labelled sandbox dispatcher: no real call, text or number is ever dialed)
- explain why an electric bill jumped (synthetic six-month history): code does the math and names the biggest cause, the model only words it, and a billing-review request is drafted, never sent
- pay a bill (demo vendor, fake money), only after two YESes, and it stops on a suspicious amount

## How we built it
- NVIDIA Nemotron on Nebius Token Factory is the model (Nano 30B A3B in the live demo), behind an OpenAI-compatible client with an offline mock fallback.
- The model only proposes a tool call as JSON. Plain code validates it. Acting tools need the person's explicit YES. The model can raise a scam flag but cannot clear a rule-based one.
- Memory uses the one-line entry format from the open Agent Memory Repo spec (each fact carries a source and date). Notes are data, never instructions: they are shown or placed in a labelled data block, never run as tool calls. Writes need YES, secrets are refused, and the demo's seed notes are invented.
- A typed decision layer: the question packs in `laya/questions` (scam screen, mail triage, intent routing) are answered by one Nemotron call each, and plain code applies the pack's confidence bands. The probabilities are the model's own, not calibrated, and this is not the Laya or Bonsai model. A payment request only warns when the sender is not on the caregiver's known-sources list. In the demo that list is invented (Lakeshore Power, Patel Family Med, Ruth Miller), the same as every other name, bill and amount.
- A small Python gateway serves a web demo. The API key stays on the server.
- Deployed free on Render.

## Results

We ran the scam screen against the live demo on 40 synthetic messages we wrote (20 scams, 20 legitimate). It flagged 20 of 20 scams and passed 18 of 20 legitimate messages. The two false alarms were real-looking Social Security and bank notices. We reran the same 40 on 2026-10-18 after the final fixes and got the same result. This is a small, hand-written set, not a benchmark. Details and every message are in docs/EVAL.md.

## Challenges
The live model first flagged a real utility bill as a scam. We fixed it with temperature 0, a 0.85 confidence bar for model-only flags, and code rules the model can't override.

While recording the demo we found and fixed more bugs: the chat model looped its output after a pasted scam, "Tell Sean I need groceries" was refused by the intent router, and a bare YES with nothing pending needed a clear answer. Each now has a regression test (199 offline tests in total as of 2026-10-19) and was checked again on the live demo. Three later assistant edge cases (spaced card or SSN digits in a saved note, a non-YES reply cancelling a pending request without saying so, and a second money request being ignored) were fixed and covered by offline tests on 2026-10-19; those fixes were checked offline and deploy health only, not on the live model route.

Optional Clairic bill reader: it only reads a pasted bill in the demo video, it is an optional text-only integration that is disabled by default, and it can only add a stop. It never approves a payment. Recorded results are in docs/CLAIRIC-BILL-TEST.md.

## What changed during the submission period
The repo started on 2026-09-19 as a local-first flow engine (scam screen, mail read-back, caregiver path, specs). The hackathon build began 2026-10-05 and added: the Nebius Token Factory client for NVIDIA Nemotron, the tool loop with YES gates, the web demo and gateway, the simulated 911 flow, memory with sources, the electric bill explainer, per-visitor session isolation, the scam eval, and the Render deployment. The dated list is in docs/CHANGES-SINCE-AUG-26.md.

## Feedback on Nebius Token Factory and NVIDIA Nemotron
- Nemotron 3 Nano 30B A3B returned empty final content on short requests until we turned thinking off with `chat_template_kwargs.enable_thinking=false`. A note about this in the quickstart would save time.
- With temperature 0 and the thinking flag off, the model followed our JSON tool format and our ordered-fact-sentence format reliably in the runs we checked. We still validate every output in code.
- Credits are Token Factory only ($50 total), which was enough for this build. GPU VMs are not covered by them.
- We did not use Nebius AI Cloud, NemoClaw, OpenShell or Hermes Agent. Geeza uses Token Factory only.

## What's next
Durable on-device memory (SQLite), voice, the on-device fast layer (Laya), and the other Nemotron models for a second opinion on scams.

## Links
- Demo: https://geeza.onrender.com (first load after idle can take about a minute)
- Code: https://github.com/ssaglin19/geeza
- Demo video: TODO (private review draft exists, not uploaded)

## Built with (tags)
NVIDIA Nemotron, Nebius Token Factory, Python, Render, OpenAI-compatible API, JSON tool calling
