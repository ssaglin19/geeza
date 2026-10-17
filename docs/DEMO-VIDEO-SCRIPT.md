# Demo video script (about 2 minutes)

Matches the cut recorded 2026-10-17 against the live app (commit f13327f). The recording is a real screen capture of https://geeza.onrender.com (mouse, typing, clicks). Open the page a minute early; the free Render instance may be asleep for about 50 seconds. Each beat below is what the live app actually does. Everything is a demo: fake emails, a fake utility vendor, a simulated payment and a simulated 911. No real money moves, no real call, text or alert is sent.

1. **Problem (10s).** "Older parents get scam emails that look real, and a wrong click costs money. Geeza is a text assistant that asks before it acts. It runs on NVIDIA Nemotron through Nebius."
2. **Mail read-back (15s).** Tap "Check my mail". Four messages are read in plain words. The fake Medicare "final notice" is flagged as a scam and not read out.
3. **Paste a scam (12s).** Type "Your account is suspended. Buy gift cards and send me the codes today or lose access." Geeza says it looks like a scam and not to reply or click, and names the signs: gift cards, pressure to act now, asks for money.
4. **Pay a bill, normal (22s).** Tap "Pay the electric bill". Geeza says it will look up the amount and waits for YES. After YES it reads $86.90, compares it with last month's $84.00 and asks YES again. After the second YES it reports "Paid $86.90 to Lakeshore Power (demo vendor, no real money moved)". Say: "This is a simulated payment to a demo vendor."
5. **Pay a bill, suspicious (15s).** Switch the scenario selector to "suspicious amount" and repeat. Geeza stops after the first YES: 412.00 is 390% above the usual 84.00, and it needs Sean to look at it.
6. **Why is my bill so high? (12s).** In the suspicious scenario, tap "Why is my electric bill so high?". Code computes the numbers, the model only orders approved facts, and Geeza writes a billing review draft that is not sent. Set the selector back to "normal" afterwards.
7. **Note to Sean (10s).** Tap "Tell Sean I need groceries". Geeza drafts the note, and after YES saves it as a draft for Sean. It is never sent by Geeza.
8. **Reminder (10s).** Tap "Remind me to take my pills at 8am", answer YES. The app says it is shown only in the demo and no phone notification is sent.
9. **Nothing to approve (7s).** Type YES with nothing waiting. Geeza says there is nothing waiting for a YES.
10. **Fall (10s).** Tap "I fell and cannot get up". A red SIMULATED 911 card shows a simulated call, an invented address and a simulated alert to Sean. Nothing is dialed or sent. Say: "This is a clearly labeled simulation."
11. **Close (5s).** "The model only proposes. Plain code checks it. Anything that acts needs the person's YES." Repo: github.com/ssaglin19/geeza.

Notes: do not say "voice" as a shipped feature. Do not call the 911 flow real. The known-sources list and the vendor are invented demo data. Reload the page between beats to clear the chat; the scenario selector is stored per browser session.
