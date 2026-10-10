"""Tool registry and model tool-call parsing for the Geeza assistant loop.

The model may only PROPOSE a tool call as JSON. Code validates it against this registry.
Tools with `acts=True` change something (spend, schedule, draft a message) and can only
run after the person says YES; no model output can mark a call as approved.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    args: dict = field(default_factory=dict)   # arg name -> short description (all strings)
    acts: bool = False                         # True = needs the person's YES before it runs


REGISTRY: dict[str, Tool] = {t.name: t for t in [
    Tool("read_mail", "Read the person's new mail aloud in plain words. Scam screen runs first."),
    Tool("scam_check", "Check one message the person pasted or forwarded for scam signs.",
         {"text": "the message to check"}),
    Tool("pay_bill", "Pay the electric bill through the registered flow. Needs two YES answers.",
         acts=True),
    Tool("set_reminder", "Set a reminder such as medication or an appointment.",
         {"what": "what to remind about", "when": "when, in the person's words"}, acts=True),
    Tool("explain_bill", "Explain why the electric bill is higher or lower than usual. Read only."),
    Tool("recall_memory", "Tell the person what you have saved about them, with where each note came from."),
    Tool("remember", "Save one short fact the person asked you to remember. Never passwords or numbers.",
         {"fact": "the fact to save, one short line"}, acts=True),
    Tool("forget", "Remove a note the person saved this visit. Needs YES.",
         {"fact": "words from the note to remove"}, acts=True),
    Tool("tell_caregiver", "Write a short note to the caregiver (Sean). Saved as a draft, never sent.",
         {"note": "what to tell the caregiver"}, acts=True),
]}

TOOL_PROMPT = (
    "You choose what to do for an older adult. Reply with JSON only, one of:\n"
    '{"tool": "<name>", "args": {...}}  or  {"reply": "<short plain answer>"}\n'
    "Tools:\n" + "\n".join(
        f"- {t.name}({', '.join(t.args)}): {t.description}" for t in REGISTRY.values()) +
    "\nPick a tool only when the person clearly asks for it. Otherwise reply."
)

MAX_ARG_LEN = 300


def parse_call(text: str) -> dict:
    """Parse a model reply into {"tool", "args"} or {"reply"}. Anything invalid becomes a reply.

    Never raises. Unknown tool names, non-string args and oversize args are rejected.
    """
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        obj = json.loads(m.group(0)) if m else None
    except ValueError:
        obj = None
    if not isinstance(obj, dict):
        return {"reply": (text or "").strip()}
    name = obj.get("tool")
    if name is None:
        return {"reply": str(obj.get("reply", "")).strip()}
    tool = REGISTRY.get(name) if isinstance(name, str) else None
    args = obj.get("args", {})
    if tool is None or not isinstance(args, dict):
        return {"reply": "I am not sure how to do that."}
    clean = {}
    for k in tool.args:
        v = args.get(k)
        if not isinstance(v, str) or not v.strip() or len(v) > MAX_ARG_LEN:
            return {"reply": f"I need a little more detail ({k})."}
        clean[k] = v.strip()
    return {"tool": tool.name, "args": clean}
