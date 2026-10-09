# Demo video shot list (draft)

Target length: about 2 minutes. Record the live demo at https://geeza.onrender.com. Open it a minute early so the free Render instance is awake (cold start is about 50 seconds). All data in the demo is synthetic; say so on camera.

Before recording: confirm Nemotron is answering and not the offline mock (a POST to /message returns model_used and fallback:false).

## Shots

1. 0:00 Say what it is. "Geeza is a text assistant for older adults. It reads mail, spots scams, and never acts without a YES." Show the page.
2. 0:10 Type "check my mail". Point out the scam message that was flagged and not read aloud.
3. 0:30 Paste the USPS redelivery text from docs/EVAL.md. Answer YES if asked. Show the scam warning.
4. 0:45 Paste a real-looking legitimate message (the Lakeshore Power bill). Show it passes.
5. 1:00 Type "pay my light bill". Show the amount shown, the two YES steps, and that the fake vendor takes fake money. Then switch to the suspicious scenario (POST /api/scenario, see gateway/server.py) and show it stops on the odd amount. Check how the page exposes this before recording.
6. 1:30 Type "I fell". Show the red SIMULATED 911 card. Say plainly that nothing is dialed.
7. 1:45 Type "Remember that I like tea". Show the note with source and date, saved only after YES.
8. 1:55 Close: Nemotron Nano on Nebius Token Factory, code owns every number and every approval, measured scam screen in docs/EVAL.md (20/20 scams flagged, 2 of 20 legitimate messages flagged), repo link.

## Say, do not say

- Say: the model proposes, plain code validates, nothing acts without YES.
- Do not say: on-device, Laya, Bonsai, production-ready, 100% recall. None of those apply to this demo.
- Probabilities come from the model and are not calibrated.

## Add if the cost-of-living flow is built

Insert after shot 5: "why is my electric bill so high?" and show the code-computed explanation and the draft billing-review request (draft only, nothing sent).
