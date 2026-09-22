# Boosh Shortcut Design

The iOS Shortcut that bridges texts to the Boosh gateway. Users import this
file; it requires no coding.

## Shortcut metadata

- **Name:** Boosh
- **Icon:** Robot face (🤖) or dog face (🐕) — friendly, not technical
- **Color:** Blue (trust, calm)
- **Description:** "Text Boosh for help with bills, family, and emergencies"

## Trigger

**Automation → Message → When I receive a message from [Boosh contact]**

- Filter: Only messages from the Boosh contact (not all messages)
- This prevents accidental triggers from other conversations

## Actions

### 1. Get message details

- **Get text from** [Shortcut Input]
- **Get sender from** [Shortcut Input]
- **Get message ID from** [Shortcut Input] (if available)

### 2. Check for group thread

- **If** [Sender] **contains** "chat" **or** [Sender] **is not** a phone number
  - **Show notification** "Boosh only works in 1:1 chats for privacy"
  - **Stop shortcut**

### 3. Send to gateway

- **URL:** `http://[gateway-ip]:8080/message`
- **Method:** POST
- **Headers:**
  - `Content-Type: application/json`
- **Request body (JSON):**
  ```json
  {
    "text": "[Message Text]",
    "sender": "[Sender]",
    "id": "[Message ID]"
  }
  ```

### 4. Handle response

- **Get** [Response] **from** [URL Result]
- **If** [Response] **contains** "error"
  - **Show notification** "Boosh had a problem. Try again or text Sean."
  - **Stop shortcut**

### 5. Send reply

- **Send** [Response.response] **to** [Sender]
- **If** [Response.actions] **contains** "emergency_call"
  - **Call** [Emergency Contact] **(optional, requires confirmation)**

## Error handling

| Error | Response |
|-------|----------|
| Gateway unreachable | "Boosh is offline. Text Sean for help." |
| Timeout (>10s) | "Boosh is thinking... try again in a moment." |
| Invalid response | "Boosh got confused. Text Sean." |
| Group thread | Silent ignore + notification to user |

## Setup instructions for users

1. **Save the Boosh contact** in your phone with the gateway number
2. **Import this shortcut** (tap the link Sean sends)
3. **Allow the shortcut** to send messages and access the network
4. **Test it:** Text "hello" to Boosh

## Privacy notes

- The shortcut only triggers for messages from the Boosh contact
- Group threads are detected and ignored
- No message content is stored on the phone (goes straight to gateway)
- The gateway can be local (your Mac) or remote (cloud Mac)

## Icon assets

- **Primary:** SF Symbol `message.badge.filled.fill`
- **Alternative:** SF Symbol `dog.fill` (if we go with the "loyal dog" branding)
- **Color:** System Blue (#007AFF)
