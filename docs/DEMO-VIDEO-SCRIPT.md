# Demo video script (about 2 minutes)

Screen: https://geeza.onrender.com (open it a minute early, it may be asleep). Show the green "Nemotron on Nebius: live" badge and the "What the engine did" panel.

1. **Problem (10s).** "Older parents get scam emails that look real, and a wrong click costs money. Geeza is a text assistant that asks before it acts."
2. **Mail read-back (20s).** Tap "Check my mail". Geeza reads 4 messages in plain words. The Medicare "final notice" is flagged as a scam and not read out. Point at the trace line: tool read_mail, model Nemotron Nano on Nebius.
3. **Paste a scam (15s).** Paste a fake "your account is suspended, send gift cards" message. Geeza says it looks like a scam and tells the person not to reply.
4. **Pay a bill, normal (25s).** Tap "Pay the electric bill". Geeza says what it will do and waits. Reply YES. It reads the amount, checks it against the usual bill, and asks YES again before paying. It pays $86.90 to the demo vendor. Say: "Demo vendor, no real money moves."
5. **Pay a bill, suspicious (20s).** Switch the scenario selector to "suspicious" and repeat. Geeza stops: 412.00 is 390% above the usual 84.00, and it asks for Sean (the caregiver). Switch the selector back to "normal" afterwards.
6. **Caregiver note and reminder (15s).** "Tell Sean I need groceries": saved as a draft, never sent. "Remind me to take my pills at 8am": waits for YES.
7. **How it is safe (15s).** "The model only proposes a tool call as JSON. Plain code checks it. Anything that acts needs the person's YES. The model can raise a scam flag but cannot clear a rule-based one."
8. **Close (5s).** Repo: github.com/ssaglin19/geeza. Built on NVIDIA Nemotron via Nebius Token Factory.

Notes: do not say "voice" as a shipped feature. The demo is text-first. Reload the page between runs to clear the chat.
