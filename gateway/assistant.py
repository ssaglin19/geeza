"""Text-in, text-out assistant brain behind the gateway's /message endpoint.

System 2 (comprehension) is Nemotron on Nebius Token Factory, replacing Bonsai for the
hackathon build. System 1 stand-in: rule screen + model screen (Laya still owns this layer
on-device). System 0 is the real flow engine; the approval gate is the engine's own
`confirm` step, answered only by an explicit YES from the person.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from boosh_flow import assist, decider, memory as mem  # noqa: E402
from boosh_flow.tools import REGISTRY, TOOL_PROMPT, parse_call  # noqa: E402
from boosh_flow.intent_router_hybrid import IntentAction, route_intent  # noqa: E402

from . import demo_data  # noqa: E402
from .vendor import run_demo_flow  # noqa: E402

DEMO_FLOW = "demo-utility-pay"
YES = re.compile(r"^\s*(yes|y|yep|yeah|ok|okay)\b[.! ]*$", re.I)
NO = re.compile(r"^\s*(no|n|cancel|stop|don'?t)\b", re.I)
MAIL = re.compile(r"\b(mail|email|emails|inbox|messages?)\b", re.I)
REMIND = re.compile(r"\bremind me (?:to |about )?(?P<what>.+?)(?: (?P<when>(?:at|on|in|tomorrow|tonight|every)\b.*))?$", re.I)
TELL = re.compile(r"\b(?:tell|message|text|let) (?:sean|my son|the caregiver)\b[ ,:]*(?:that |about )?(?P<note>.*)", re.I)
SCAM_Q = re.compile(r"\b(is this|is that|check)\b.*\bscam\b|\bscam\b.*\?", re.I)
RECALL = re.compile(r"\bwhat (?:do|have) you (?:remember|know|saved?)\b|\bwhat did i (?:tell|ask) you to remember\b", re.I)
REMEMBER = re.compile(r"^\s*(?:please )?remember (?:that )?(?P<fact>.+)$", re.I)
FORGET = re.compile(r"^\s*(?:please )?forget (?:that |about )?(?P<fact>.+)$", re.I)
SEED_DIR = Path(__file__).resolve().parents[1] / "memory" / "demo-memory"
BILL = re.compile(r"\b(pay|paying)\b.*\b(bill|electric|light|power)\b|\b(electric|power|light) bill\b", re.I)


class Assistant:
    def __init__(self, client, scenario: str = "normal"):
        self.client = client
        self.scenario = scenario
        self.last_tool = None
        self.last_intent = None
        self.pending: dict[str, dict] = {}   # sender -> {"kind": "offer"|"approval", ...}
        self.history: dict[str, list] = {}
        self.reminders: dict[str, list] = {}
        self.drafts: dict[str, list] = {}
        self.seed = mem.load_seed(SEED_DIR)          # caregiver-installed, read-only
        self.notes: dict[str, list] = {}             # saved by the person this session (RAM only)

    def _entries(self, sender):
        return self.seed + self.notes.get(sender, [])

    def _meta(self, extra=None):
        d = {"model_used": getattr(self.client, "last_model", None),
             "fallback": bool(getattr(self.client, "used_fallback", False))}
        d.update(extra or {})
        return d

    def handle(self, text: str, sender: str = "demo") -> dict:
        p = self.pending.get(sender)
        if p:
            if YES.match(text):
                return self._on_yes(sender, p)
            if NO.match(text):
                self.pending.pop(sender, None)
                return {"response": "Okay, I did not do it.", "actions": [], **self._meta()}
            self.pending.pop(sender, None)  # any other text cancels a pending offer/approval

        routed = self._route(text, sender)
        if routed:
            return routed
        return self._after_route(text, sender)

    def _after_route(self, text: str, sender: str) -> dict:
        call = self._choose(text)
        self.last_tool = call.get("tool")
        if "tool" not in call:
            if call.get("reply"):
                return {"response": call["reply"], "actions": [], **self._meta()}
            return self._chat(text, sender)
        return self._dispatch(call["tool"], call["args"], sender, text)

    SKILL_ASK = {"handle_bills": "deal with a bill", "check_schedule": "check your schedule or reminders",
                 "contact_family": "reach family", "get_groceries": "order groceries",
                 "check_safety": "check if something is a scam", "emergency": "get urgent help"}

    def _route(self, text: str, sender: str) -> dict | None:
        """System 1: intent-routing pack (bands: high >= 0.80 go, 0.50-0.79 ask, < 0.50 general).
        Returns a reply when routing decides, else None and the normal tool choice runs.
        Memory commands skip it (code-first). Probabilities are self-reported by Nemotron."""
        if RECALL.search(text) or REMEMBER.match(text) or FORGET.match(text):
            return None
        if not getattr(self.client, "live", False):
            return None
        d = decider.decide("intent-routing", text, self.client)
        if not d["ok"]:
            return None
        r = decider.intent_policy(d["answers"])
        self.last_intent = r
        meta = {**self._meta(), "intent": r}
        if r["skill"] == "emergency":
            return {"response": "This sounds urgent. If you are in danger or hurt, call 911 now. "
                                "This demo cannot call or text anyone for you.",
                    "actions": [{"type": "emergency_notice"}], **meta}
        if r["skill"] == "get_groceries":
            return {"response": "I cannot order groceries in this demo.", "actions": [], **meta}
        if r["band"] == "medium" and r["skill"] in self.SKILL_ASK:
            self.pending[sender] = {"kind": "intent", "text": text}
            return {"response": f"Did you want to {self.SKILL_ASK[r['skill']]}? Reply YES to go on.",
                    "actions": [{"type": "confirm_intent", "skill": r["skill"]}], **meta}
        return None

    def _choose(self, text: str) -> dict:
        """Pick a tool. Live model proposes JSON; code validates. With no key, keyword stand-in."""
        # Explicit memory commands are matched by code first, so the model cannot ask for a YES
        # that nothing is waiting on. Only text that STARTS with the command counts.
        if RECALL.search(text) or REMEMBER.match(text) or FORGET.match(text):
            return self._keyword_choice(text)
        if getattr(self.client, "live", False):
            raw = self.client.complete(
                [{"role": "system", "content": TOOL_PROMPT}, {"role": "user", "content": text}],
                max_tokens=400)
            if not getattr(self.client, "used_fallback", False):
                call = parse_call(raw)
                if "tool" in call:
                    return call
                # Plain-text answers pass through. Cut-off or malformed JSON never reaches the person.
                if call.get("reply") and not raw.lstrip().startswith(("{", "[")):
                    return call
        return self._keyword_choice(text)

    def _keyword_choice(self, text: str) -> dict:
        if SCAM_Q.search(text) and len(text) > 40:
            return {"tool": "scam_check", "args": {"text": text}}
        if MAIL.search(text):
            return {"tool": "read_mail", "args": {}}
        if RECALL.search(text):
            return {"tool": "recall_memory", "args": {}}
        m = FORGET.match(text)
        if m:
            return {"tool": "forget", "args": {"fact": m.group("fact").strip().rstrip(".")}}
        m = REMEMBER.match(text)
        if m:
            return {"tool": "remember", "args": {"fact": m.group("fact").strip().rstrip(".")}}
        m = REMIND.search(text)
        if m:
            return {"tool": "set_reminder", "args": {"what": m.group("what"), "when": m.group("when") or "when I say"}}
        m = TELL.search(text)
        if m and m.group("note").strip():
            return {"tool": "tell_caregiver", "args": {"note": m.group("note").strip()}}
        if BILL.search(text):
            # Laya's 3-class skill model is not loaded here; the keyword match stands in for it.
            r = route_intent(laya_skill="handle_bills", laya_confidence=0.9, laya_probs={},
                             text=text, available_flows={"consumers-energy-pay"})
            if r.action == IntentAction.LAUNCH_FLOW:
                return {"tool": "pay_bill", "args": {}}
        return {}

    def _dispatch(self, name: str, args: dict, sender: str, text: str) -> dict:
        tool = REGISTRY[name]
        if name == "read_mail":
            out = self._mail()
            out["tool"] = name
            return out
        if name == "recall_memory":
            es = self._entries(sender)
            body = "\n".join(mem.format_entry(e) for e in es) or "Nothing yet."
            return {"response": "Here is what I have saved:\n" + body, "actions": [{"type": "recall", "count": len(es)}],
                    "tool": name, **self._meta()}
        if name == "remember":
            why = mem.check_fact(args["fact"])
            if why:
                return {"response": f"I did not save that: {why}.", "actions": [], "tool": name, **self._meta()}
            if any(e["text"].lower() == args["fact"].strip().lower() for e in self._entries(sender)):
                return {"response": "I already have that saved.", "actions": [], "tool": name, **self._meta()}
            self.pending[sender] = {"kind": "remember", "args": args}
            return {"response": f'Save this note: "{args["fact"]}"? Reply YES to save it.',
                    "actions": [{"type": "confirm", "tool": name}], "tool": name, **self._meta()}
        if name == "forget":
            hits = [e for e in self.notes.get(sender, []) if args["fact"].lower() in e["text"].lower()]
            if not hits:
                return {"response": "I have no note of yours like that. Notes set up by your caregiver "
                                    "can only be changed by Sean.", "actions": [], "tool": name, **self._meta()}
            self.pending[sender] = {"kind": "forget", "args": args}
            return {"response": f'Remove this note: "{hits[0]["text"]}"? Reply YES to remove it.',
                    "actions": [{"type": "confirm", "tool": name}], "tool": name, **self._meta()}
        if name == "scam_check":
            e = {"from": "", "subject": "", "body": args["text"]}
            r = assist.scam_screen(e, self.client)
            msg = ("This looks like a scam. Do not reply or click anything. " + "; ".join(r["reasons"]) + "."
                   if r["flagged"] else ("This might be a scam, so be careful. Do not reply or click until Sean has looked at it."
                      if r.get("soft_warning") else
                      "I did not find scam signs, but if it asks for money or codes, stop and ask Sean."))
            return {"response": msg, "actions": [{"type": "scam_check", "flagged": r["flagged"]}],
                    "tool": name, **self._meta()}
        # Acting tools: never run before the person says YES.
        if name == "pay_bill":
            self.pending[sender] = {"kind": "offer"}
            return {"response": "I can pay your electric bill. First I will look up the amount "
                                "and check it. Reply YES to start.",
                    "actions": [{"type": "flow_offer", "flow_id": DEMO_FLOW}], "tool": name, **self._meta()}
        if name == "set_reminder":
            self.pending[sender] = {"kind": "reminder", "args": args}
            return {"response": f"Set a reminder to {args['what']}, {args['when']}? Reply YES to set it.",
                    "actions": [{"type": "confirm", "tool": name}], "tool": name, **self._meta()}
        if name == "tell_caregiver":
            self.pending[sender] = {"kind": "draft", "args": args}
            return {"response": f'Draft note to Sean: "{args["note"]}". Reply YES to save it. '
                                "I never send it by myself.",
                    "actions": [{"type": "confirm", "tool": name}], "tool": name, **self._meta()}
        raise AssertionError(f"unhandled tool {tool.name}")

    def _chat(self, text: str, sender: str) -> dict:
        h = self.history.setdefault(sender, [])
        h.append({"role": "user", "content": text})
        out = assist.chat(h, self.client, mem.as_data_block(self._entries(sender)))
        h.append({"role": "assistant", "content": out["reply"]})
        return {"response": out["reply"], "actions": [], **self._meta()}

    def _mail(self) -> dict:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=len(demo_data.EMAILS)) as ex:
            results = list(ex.map(lambda e: assist.read_back(e, self.client), demo_data.EMAILS))
        items = []
        for e, r in zip(demo_data.EMAILS, results):
            t = r.get("triage") or {}
            items.append({"id": e["id"], "from": e["from"], "subject": e["subject"],
                          "spoken": r["spoken"], "scam": r["screen"]["flagged"],
                          "reasons": r["screen"]["reasons"], "category": t.get("category"),
                          "urgency": t.get("urgency"), "needs_reply": t.get("needs_reply")})
        n_scam = sum(i["scam"] for i in items)
        lines = [f"You have {len(items)} messages." + (f" {n_scam} looks like a scam and I did not read it." if n_scam else "")]
        for i in items:
            lines.append(f"- {i['subject']}: {i['spoken']}")
        return {"response": "\n".join(lines), "actions": [{"type": "mail", "items": items}], **self._meta()}

    def _run(self, approver):
        amount = demo_data.SCENARIOS.get(self.scenario, demo_data.SCENARIOS["normal"])
        return run_demo_flow(amount, demo_data.LAST_BILL, approver)

    def _on_yes(self, sender: str, p: dict) -> dict:
        if p["kind"] == "intent":
            self.pending.pop(sender, None)
            return self._after_route(p["text"], sender)
        if p["kind"] == "reminder":
            self.pending.pop(sender, None)
            self.reminders.setdefault(sender, []).append(p["args"])
            return {"response": f"Done. I will remind you to {p['args']['what']}, {p['args']['when']}. "
                                "(Demo: shown here, no phone notification is sent.)",
                    "actions": [{"type": "reminder_set", **p["args"]}], "tool": "set_reminder", **self._meta()}
        if p["kind"] == "forget":
            self.pending.pop(sender, None)
            keep = [e for e in self.notes.get(sender, []) if p["args"]["fact"].lower() not in e["text"].lower()]
            n = len(self.notes.get(sender, [])) - len(keep)
            self.notes[sender] = keep
            return {"response": f"Removed {n} note." if n == 1 else f"Removed {n} notes.",
                    "actions": [{"type": "memory_forgotten", "count": n}], "tool": "forget", **self._meta()}
        if p["kind"] == "remember":
            self.pending.pop(sender, None)
            if mem.check_fact(p["args"]["fact"]):
                return {"response": "I did not save that.", "actions": [], **self._meta()}
            e = mem.new_entry(p["args"]["fact"])
            self.notes.setdefault(sender, []).append(e)
            return {"response": f"Saved. {mem.format_entry(e)} (Demo: kept for this visit only.)",
                    "actions": [{"type": "memory_saved", **e}], "tool": "remember", **self._meta()}
        if p["kind"] == "draft":
            self.pending.pop(sender, None)
            self.drafts.setdefault(sender, []).append(p["args"])
            return {"response": "Saved the note as a draft for Sean. It has not been sent.",
                    "actions": [{"type": "draft_saved", **p["args"]}], "tool": "tell_caregiver", **self._meta()}
        if p["kind"] == "offer":
            # Dry run up to the approval gate: the approver always says no, so nothing is paid.
            seen = {}
            def ask(q): seen.update(q); return False
            events, paid = self._run(ask)
            if "amount_key" not in seen:
                self.pending.pop(sender, None)
                gate = next((e for e in events if e["event"] == "GATE_FAILED"), None)
                why = gate["detail"] if gate else "the bill page did not look right"
                return {"response": f"I stopped before paying. {why}. This needs Sean to look at it.",
                        "actions": [{"type": "escalate", "reason": why}], "events": events, **self._meta()}
            amount = next(e["value"] for e in events if e["event"] == "READ")
            self.pending[sender] = {"kind": "approval", "amount": amount}
            return {"response": f"Your Lakeshore Power bill is ${amount}. Last month was "
                                f"${demo_data.LAST_BILL:.2f}, so that looks normal. Reply YES to pay ${amount}.",
                    "actions": [{"type": "approval", "amount": amount}], "events": events, **self._meta()}
        # Approval: the person's YES covers only the amount they were shown.
        quoted = p["amount"]
        def approve(q): return q.get("kind") == "approval" and self._amount_now() == quoted
        events, paid = self._run(approve)
        self.pending.pop(sender, None)
        if paid:
            return {"response": f"Paid ${quoted} to Lakeshore Power (demo vendor, no real money moved).",
                    "actions": [{"type": "paid", "amount": quoted}], "events": events, **self._meta()}
        return {"response": "The amount changed, so I did not pay. Ask me again.",
                "actions": [], "events": events, **self._meta()}

    def _amount_now(self) -> str:
        return demo_data.SCENARIOS.get(self.scenario, demo_data.SCENARIOS["normal"])
