"""Flow schema: dataclasses, loading, and static validation."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Anchor:
    selector: str | None = None
    text: str | None = None
    weight: float = 1.0


@dataclass
class MatchSpec:
    url_host: str | None = None      # hard gate: exact host match
    url_contains: str | None = None  # path+query substring, checked after host
    anchors: list[Anchor] = field(default_factory=list)


@dataclass
class Step:
    action: str
    params: dict = field(default_factory=dict)


@dataclass
class PageSpec:
    name: str
    match: MatchSpec
    steps: list[Step] = field(default_factory=list)


@dataclass
class Flow:
    name: str
    vendor: str = ""
    entry_url: str = ""
    version: int = 1
    spends: bool = False
    thresholds: dict = field(default_factory=lambda: {"act": 0.85, "confirm": 0.5})
    pages: list[PageSpec] = field(default_factory=list)


def load_flow(path: str | Path) -> Flow:
    return flow_from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def flow_from_dict(d: dict) -> Flow:
    flow = Flow(
        name=d["name"],
        vendor=d.get("vendor", ""),
        entry_url=d.get("entry_url", ""),
        version=d.get("version", 1),
        spends=d.get("spends", False),
        thresholds={**{"act": 0.85, "confirm": 0.5}, **d.get("thresholds", {})},
    )
    for p in d.get("pages", []):
        m = p.get("match", {})
        anchors = [Anchor(**a) for a in m.get("anchors", [])]
        match = MatchSpec(url_host=m.get("url_host"), url_contains=m.get("url_contains"), anchors=anchors)
        steps = [Step(action=s["action"], params=s.get("params", {})) for s in p.get("steps", [])]
        flow.pages.append(PageSpec(name=p["name"], match=match, steps=steps))
    return flow


def validate_flow(flow: Flow) -> list[str]:
    """Static checks run at load time. The app refuses to register a flow with errors."""
    errors: list[str] = []
    if not flow.entry_url:
        errors.append("entry_url is required")
    if not flow.pages:
        errors.append("flow needs at least one page")
    has_confirm = False
    for page in flow.pages:
        if len(page.match.anchors) < 3:
            errors.append(f"page '{page.name}': fewer than 3 anchors")
        if not page.match.url_host:
            errors.append(f"page '{page.name}': missing url_host (hard gate)")
        if not page.match.url_contains:
            errors.append(f"page '{page.name}': missing url_contains path check")
        if not page.steps:
            errors.append(f"page '{page.name}': no steps")
        for step in page.steps:
            if step.action == "confirm":
                has_confirm = True
    if flow.spends and not has_confirm:
        errors.append("flow moves money (spends=true) but has no confirm step")
    return errors
