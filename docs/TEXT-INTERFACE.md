# Text-Message Interface — The Real Product

## The insight

The users don't know another alternative exists. They won't download an app,
learn a new interface, or change their behavior. But they already text message
every day. The product is not an app — it's a **contact in their phone** that
happens to be an AI.

## What this changes

| Before (app-first) | After (text-first) |
|---|---|
| Native iOS app, App Store, SwiftUI | SMS/iMessage bot, no install |
| Voice-first (speech in/out) | Text-first, voice optional |
| One screen, huge type | Their existing Messages app |
| Approval gate UI in app | "Reply YES to confirm" |
| WKWebView in-app browser | Links sent via text, opened in Safari |
| Caregiver escalation in app | Caregiver is just another text thread |

## The architecture shift

**System 0 (execute):** Unchanged — deterministic flows, approval gates,
escalation. But the "browser" is now Safari on their phone, driven by links
we send. We can't drive Safari (iOS limitation), but we can send a link that
opens to a specific page with instructions.

**System 1 (decide):** Unchanged — Laya/Needle for intent routing, scam
screening, mail triage. Runs on-device or on a home server.

**System 2 (comprehend):** Unchanged — Bonsai for conversation, reading,
explaining. But now it's generating text responses, not voice.

**New component — the gateway:** A service that receives texts, routes them
through the stack, and sends responses. Options:

| Option | How it works | Privacy | Cost |
|--------|-----------|---------|------|
| **iMessage extension** | App extension that reads/sends iMessages | On-device | Free |
| **SMS gateway (Twilio)** | Cloud service forwards texts to our server | **Cloud middleman** | ~$0.01/msg |
| **Home server + email** | Texts forwarded to email, processed locally | On-device | Free |
| **Apple Business Chat** | Official Apple channel for businesses | Apple servers | Free |

**The privacy constraint kills Twilio** — any cloud SMS gateway is a middleman.
iMessage extension is the only truly private option, but requires an app install
(which they won't do). **Apple Business Chat** is the compromise: Apple is
already the middleman for iMessage, so no new third party is introduced.

## The user experience

**Them:** "What's the weather today?"
**Bot:** "High of 72, low of 54. Rain after 6pm. Want me to remind you to take
an umbrella when you leave?"

**Them:** "Pay the electric bill"
**Bot:** "Your Consumers Energy bill is $87.43, due Oct 15. Reply YES to pay
it now, or CALL to pay over the phone."

**Them:** "YES"
**Bot:** "Paid. Confirmation #CE-8847291. I'll remind you when the next bill
arrives."

**Them:** "Is this email a scam?" [forwards email]
**Bot:** "Yes. Do not click any links. This is a fake Medicare scam. I've
deleted it. Want me to tell Sean about this?"

## What we build

1. **The bot brain** — the existing System 0/1/2 stack, wrapped in a
   text-in/text-out interface. Already built.

2. **The gateway** — the piece that connects to iMessage/SMS. This is new.
   Options:
   - **v1:** Apple Business Chat (official, no new middleman)
   - **v2:** iMessage extension (fully on-device, requires app install)
   - **v3:** Home server with email forwarding (fully private, complex setup)

3. **The link handler** — when a flow needs a browser (bill pay), we send a
   link that opens Safari with instructions. The user completes the flow
   manually, or we use Apple Pay / in-app purchase for the actual transaction.

## What we don't build

- A native app (they won't install it)
- A voice interface (they won't use it)
- A web dashboard (they won't open it)

## The hard problems

1. **Browser automation without an app.** We can't drive Safari. Options:
   - Send a link with pre-filled credentials (insecure, bad)
   - Use Apple Pay / in-app purchase for payments (limited vendors)
   - Walk them through it via text ("Tap the link, then tap Pay, then tell me
     the confirmation number")
   - **The honest answer:** v1 is read-only + reminders. Purchases happen
     manually with our guidance.

2. **Rich content in texts.** SMS is 160 chars, no formatting. iMessage
   supports rich links, images, and Apple Pay. The experience is better on
   iMessage, but we can't control which they use.

3. **Group threads.** If they add the bot to a family group chat, privacy
   is compromised. The bot must only respond to direct messages.

## The v1 scope (revised)

1. **Text in/out** — answer questions, tell time, weather, simple math
2. **Reminders** — "Remind me to take my pill at 6pm" → local notification
3. **Scam screen** — forward a suspicious text/email, get a verdict
4. **Mail read-back** — "Read my email" → summary of inbox
5. **Bill reminders** — "Your electric bill is due Friday" → text reminder
6. **Emergency** — "I fell" → call 911 + text caregiver

**Out of scope for v1:**
- Actual bill payment (manual with guidance)
- Calendar management (read-only for v1)
- Grocery ordering (manual with guidance)

## The build order

1. **Gateway** — Apple Business Chat integration, or iMessage extension
2. **Bot brain wrapper** — text interface to existing stack
3. **Link handler** — Safari links with instructions
4. **Notification bridge** — local reminders via text

## Open questions

- Apple Business Chat requires a business account and approval. Personal use
  may not qualify.
- iMessage extension requires an app install, which they won't do. Is there
  a way to sideload without App Store?
- Can we use Shortcuts.app to bridge texts to a local server? (User installs
  a Shortcut, not an app — lower friction.)

## Decision needed

The gateway choice determines everything downstream. Apple Business Chat is
the cleanest privacy story but may not be available. iMessage extension is
the best UX but requires app install. Shortcuts is the middle ground.

**Recommendation:** Prototype the Shortcuts bridge first — it's the lowest
friction for the user (install a Shortcut, not an app), keeps everything
on-device, and doesn't require Apple approval. If it works, it's v1. If not,
fall back to Apple Business Chat.
