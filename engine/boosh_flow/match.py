"""Page matching: weighted anchors behind a hard HOST gate, then a path check."""
from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlsplit

from .schema import PageSpec


@dataclass
class MatchResult:
    page: str
    confidence: float
    matched: list = field(default_factory=list)
    failed: list = field(default_factory=list)


def _host(url: str) -> str:
    try:
        return (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def _path_and_query(url: str) -> str:
    try:
        parts = urlsplit(url)
    except ValueError:
        return ""
    return (parts.path or "") + (f"?{parts.query}" if parts.query else "")


def anchor_hit(snapshot: dict, anchor) -> bool:
    for el in snapshot.get("elements", []):
        if anchor.selector is not None and el.get("selector") == anchor.selector:
            return True
        if anchor.text is not None and anchor.text.lower() in (el.get("text") or "").lower():
            return True
    return False


def page_confidence(snapshot: dict, page: PageSpec) -> MatchResult:
    m = page.match
    url = snapshot.get("url") or ""
    # Hard gate 1: exact host. Anchors alone never identify a page — a phishing
    # lookalike can reproduce any DOM, but it cannot live on the real domain.
    if m.url_host and _host(url) != m.url_host.lower():
        return MatchResult(page.name, 0.0, [], ["host"])
    # Hard gate 2: path substring, checked against path+query only.
    if m.url_contains and m.url_contains not in _path_and_query(url):
        return MatchResult(page.name, 0.0, [], ["path"])
    if not m.anchors:
        return MatchResult(page.name, 1.0, [], [])
    total = sum(a.weight for a in m.anchors)
    matched, failed, hit_weight = [], [], 0.0
    for a in m.anchors:
        label = a.selector or a.text
        if anchor_hit(snapshot, a):
            matched.append(label)
            hit_weight += a.weight
        else:
            failed.append(label)
    return MatchResult(page.name, round(hit_weight / total, 4), matched, failed)


def best_page_match(flow, snapshot: dict):
    """Return (page, result) with the highest confidence above zero, else None."""
    best = None
    for page in flow.pages:
        result = page_confidence(snapshot, page)
        if result.confidence <= 0.0:
            continue
        if best is None or result.confidence > best[1].confidence:
            best = (page, result)
    return best
