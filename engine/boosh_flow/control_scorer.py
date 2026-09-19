"""Control scoring: GLiNER2-inspired approach to page matching.

Instead of fixed anchors, score page controls (buttons, links, inputs) by
how well they match the flow's intent. More resilient to site redesigns —
the model learns "what a pay button looks like" rather than "this exact
selector must exist."

This is a prototype: the real implementation would use GLiNER2 or a similar
entity extraction model. For now, it uses TF-IDF + cosine similarity as a
stand-in to validate the architecture.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Control:
    """A page control (button, link, input) with its observable properties."""
    tag: str           # button, a, input, select
    text: str          # visible text or label
    aria_label: str    # accessibility label
    href: str          # for links
    input_type: str    # for inputs: text, password, submit, etc.
    selector: str      # CSS selector for execution


@dataclass
class ControlScore:
    control: Control
    score: float       # 0.0 to 1.0
    matched_terms: list


class ControlScorer(Protocol):
    """Protocol for control scoring implementations."""
    def score(self, controls: list[Control], intent: str) -> list[ControlScore]:
        """Score controls by relevance to the intent (e.g., 'pay bill', 'log in')."""
        ...


class TfidfControlScorer:
    """TF-IDF + cosine similarity scorer. Stand-in for GLiNER2."""

    def __init__(self):
        self.intent_terms = {
            "pay bill": ["pay", "payment", "bill"],
            "log in": ["log", "sign", "in"],
            "check balance": ["balance", "account", "summary"],
            "order groceries": ["cart", "checkout", "order"],
            "refill prescription": ["refill", "prescription", "pharmacy"],
        }

    def score(self, controls: list[Control], intent: str) -> list[ControlScore]:
        terms = self.intent_terms.get(intent, intent.lower().split())
        scores = []
        for control in controls:
            text = f"{control.text} {control.aria_label}".lower()
            matched = [t for t in terms if t in text]
            # Simple scoring: fraction of terms matched, weighted by control type
            base = len(matched) / len(terms) if terms else 0.0
            # Buttons and submit inputs are more likely to be actions
            if control.tag == "button" or control.input_type == "submit":
                base *= 1.2
            # Links are less likely to be primary actions
            elif control.tag == "a":
                base *= 0.8
            scores.append(ControlScore(control, min(base, 1.0), matched))
        return sorted(scores, key=lambda s: s.score, reverse=True)


def extract_controls(snapshot: dict) -> list[Control]:
    """Extract controls from a page snapshot (same format as flow engine)."""
    controls = []
    for el in snapshot.get("elements", []):
        tag = el.get("tag", "")
        if tag not in ("button", "a", "input", "select"):
            continue
        controls.append(Control(
            tag=tag,
            text=el.get("text", ""),
            aria_label=el.get("aria-label", ""),
            href=el.get("href", ""),
            input_type=el.get("type", ""),
            selector=el.get("selector", ""),
        ))
    return controls


def best_control(snapshot: dict, intent: str, scorer: ControlScorer = None) -> ControlScore | None:
    """Find the best control for an intent, or None if nothing scores well."""
    if scorer is None:
        scorer = TfidfControlScorer()
    controls = extract_controls(snapshot)
    if not controls:
        return None
    scores = scorer.score(controls, intent)
    if not scores or scores[0].score < 0.2:
        return None
    return scores[0]
