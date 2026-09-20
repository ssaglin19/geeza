# Shortcuts Bridge — Text Message to Boosh Gateway

## Overview

The Shortcuts bridge forwards incoming text messages to a local server running
the Boosh stack. No app install required — the user creates one Shortcut and
one Automation, and texts flow to the assistant.

## Components

1. **Boosh Gateway** — local HTTP server (Python/Flask) that receives texts,
   runs them through System 0/1/2, and returns responses
2. **Shortcut** — "Send to Boosh" — shares a message to the gateway
3. **Automation** — "When I receive a message" — triggers the Shortcut

## The Gateway Server

A lightweight HTTP server that runs on the user's Mac (or any always-on
machine on the local network). Receives POST requests from the Shortcut,
processes the message, returns a response.

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check — returns `{"status": "ok"}` |
| `/message` | POST | Receive a text message, return a response |
| `/config` | GET | Return current configuration (for debugging) |

### POST /message

**Request:**
```json
{
  "text": "What's the weather today?",
  "sender": "+15551234567",
  "timestamp": "2026-09-20T14:32:00Z",
  "message_id": "msg_abc123"
}
```

**Response:**
```json
{
  "response": "It's 72°F and sunny in Detroit. No jacket needed.",
  "actions": [],
  "confidence": 0.94
}
```

**Response with action (bill pay):**
```json
{
  "response": "Your Consumers Energy bill is $87.43, due Oct 3. Say 'pay it' to proceed.",
  "actions": [
    {
      "type": "bill_summary",
      "vendor": "Consumers Energy",
      "amount": 87.43,
      "due_date": "2026-10-03",
      "flow_id": "consumers-energy-pay"
    }
  ],
  "confidence": 0.91
}
```

**Response with approval request:**
```json
{
  "response": "Ready to pay $87.43 to Consumers Energy. Reply YES to confirm, NO to cancel.",
  "actions": [
    {
      "type": "approval_request",
      "flow_id": "consumers-energy-pay",
      "amount": 87.43,
      "vendor": "Consumers Energy",
      "approval_token": "tok_xyz789"
    }
  ],
  "confidence": 0.95
}
```

## The Shortcut

**Name:** Send to Boosh

**Inputs:** Text message (from Share Sheet or Automation)

**Actions:**

1. **Get text from input** — the message body
2. **Get sender** — the phone number or contact name
3. **Get current date** — ISO 8601 timestamp
4. **Generate UUID** — message ID for deduplication
5. **Create dictionary** — the JSON payload
6. **Get contents of URL** — POST to `http://boosh-gateway.local:8080/message`
   - Method: POST
   - Headers: `Content-Type: application/json`
   - Request Body: the dictionary
7. **Get dictionary value** — extract `response` from the JSON
8. **Show notification** — display the response (for manual trigger)
9. **Send message** — reply to the sender (for automation trigger)

## The Automation

**Name:** Boosh Auto-Reply

**Trigger:** When I receive a message

**Conditions:**
- Sender is not in a group thread (privacy guard)
- Message contains text (not just an image or reaction)

**Actions:**
1. Run "Send to Boosh" Shortcut
2. Wait for response
3. Send reply to sender

**Privacy guard:** The automation checks if the message is from a group
thread. If it is, it does nothing — the bot stays silent in groups.

## Setup Instructions (for the user)

1. **Install the gateway** — one-time setup on a Mac or always-on PC:
   ```bash
   pip install boosh-gateway
   boosh-gateway start
   ```

2. **Create the Shortcut:**
   - Open Shortcuts app
   - Tap + to create new
   - Add actions: Text → Dictionary → URL → Show Notification
   - Name it "Send to Boosh"

3. **Create the Automation:**
   - Shortcuts → Automation → +
   - Trigger: Message
   - Action: Run "Send to Boosh"
   - Turn off "Ask Before Running"

4. **Test:**
   - Send a text to yourself: "What's the weather?"
   - The bot should reply within seconds

## Security

- The gateway binds to `127.0.0.1` by default (localhost only)
- For LAN access (Mac server + iPhone client), bind to the local IP with
  a shared secret token in the `X-Boosh-Token` header
- No authentication for localhost (physical access = trust)
- Token auth for LAN (prevents random devices on the network from using it)

## Failure Modes

| Failure | Behavior |
|---------|----------|
| Gateway offline | Shortcut shows "Boosh is unavailable" notification |
| Timeout (>5s) | Returns "I'm thinking... try again in a moment" |
| Low confidence | Returns "I'm not sure — call Sean?" |
| Flow aborted | Returns "I couldn't complete that. Let's try something else." |
| Emergency detected | Bypasses all processing, returns "Calling 911 now" |

## Implementation

See `gateway/server.py` for the reference implementation (Python/Flask).
The server wraps the existing Boosh stack:

- `engine/` — flow engine, mail router, intent router, escalation
- `laya/` — scam screen, mail triage (when fine-tuned)
- `memory/` — SQLite corpus (when installed)

The gateway is the **glue** between the text-message interface and the
existing Boosh architecture.