"""Boosh flow engine — deterministic System 0 reference implementation.

Python mirror of the Swift port (see ios/README.md). Stdlib only.
The browser driver is abstract; the real one is WKWebView + JS bridge on iOS.
"""
from .schema import Anchor, Flow, MatchSpec, PageSpec, Step, load_flow, validate_flow
from .match import MatchResult, best_page_match, page_confidence
from .router import ABORT, ACT, CONFIRM, band
from .gates import amount_sanity, evaluate_gate
from .engine import Driver, run_flow

__all__ = [
    "Anchor", "Flow", "MatchSpec", "PageSpec", "Step",
    "load_flow", "validate_flow",
    "MatchResult", "best_page_match", "page_confidence",
    "ABORT", "ACT", "CONFIRM", "band",
    "amount_sanity", "evaluate_gate",
    "Driver", "run_flow",
]
