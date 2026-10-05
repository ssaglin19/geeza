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
from boosh_flow import assist  # noqa: E402
from boosh_flow.intent_router_hybrid import IntentAction, route_intent  # noqa: E402

from . import demo_data  # noqa: E402
from .vendor import run_demo_flow  # noqa: E402

DEMO_FLOW = "demo-utility-pay"
YES = re.compile(r"^\s*(yes|y|yep|yeah|ok|okay)\b[.! ]*$", re.I)
NO = re.compile(r"^\s*(no|n|cancel|stop|don'?t)\b", re.I)
MAIL = re.compile(r"\b(mail|email|emails|inbox|messages?)\b", re.I)
BILL = re.compile(r"\b(pay|paying)\b.*\b(bill|electric|light|power)\b|\b(electric|power|light) bill\b", re.I)


class Assistant:
    def __init__(self, client, scenario: str = "normal"):
        self.client = client
        self.scenario = scenario
        self.pending: dict[str, dict] = {}   # sender -> {"kind": "offer"|"approval", ...}
        self.history: dict[str, list] = {}

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
                return {"response": "Okay, I did not pay anything.", "actions": [], **self._meta()}
            self.pending.pop(sender, None)  # any other text cancels a pending offer/approval

        if MAIL.search(text):
            return self._mail()

        # Laya's 3-class skill model is not loaded here; a keyword stand-in picks the skill.
        skill, conf = ("handle_bills", 0.9) if BILL.search(text) else ("general_help", 0.5)
        result = route_intent(laya_skill=skill, laya_confidence=conf, laya_probs={},
                              text=text, available_flows={"consumers-energy-pay"})
        if result.action == IntentAction.LAUNCH_FLOW and result.flow_id == "consumers-energy-pay":
            self.pending[sender] = {"kind": "offer"}
            return {"response": "I can pay your electric bill. First I will look up the amount "
                                "and check it. Reply YES to start.",
                    "actions": [{"type": "flow_offer", "flow_id": DEMO_FLOW}], **self._meta()}
        if result.action == IntentAction.EMERGENCY:
            return {"response": result.message, "actions": [{"type": "emergency_call", "number": "911"}],
                    **self._meta()}

        h = self.history.setdefault(sender, [])
        h.append({"role": "user", "content": text})
        out = assist.chat(h, self.client)
        h.append({"role": "assistant", "content": out["reply"]})
        return {"response": out["reply"], "actions": [], **self._meta()}

    def _mail(self) -> dict:
        items = []
        for e in demo_data.EMAILS:
            r = assist.read_back(e, self.client)
            items.append({"id": e["id"], "from": e["from"], "subject": e["subject"],
                          "spoken": r["spoken"], "scam": r["screen"]["flagged"],
                          "reasons": r["screen"]["reasons"]})
        n_scam = sum(i["scam"] for i in items)
        lines = [f"You have {len(items)} messages." + (f" {n_scam} looks like a scam and I did not read it." if n_scam else "")]
        for i in items:
            lines.append(f"- {i['subject']}: {i['spoken']}")
        return {"response": "\n".join(lines), "actions": [{"type": "mail", "items": items}], **self._meta()}

    def _run(self, approver):
        amount = demo_data.SCENARIOS.get(self.scenario, demo_data.SCENARIOS["normal"])
        return run_demo_flow(amount, demo_data.LAST_BILL, approver)

    def _on_yes(self, sender: str, p: dict) -> dict:
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
