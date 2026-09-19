"""Flow executor. Every decision is code; every event is logged."""
from __future__ import annotations

from abc import ABC, abstractmethod

from .gates import evaluate_gate
from .match import best_page_match
from .router import ABORT, ACT, CONFIRM, band
from .schema import Flow, Step

MAX_STEPS = 60


class Driver(ABC):
    """Abstract browser driver. iOS: WKWebView + JS bridge. Tests: scripted fixtures."""

    @abstractmethod
    def goto(self, url: str) -> None: ...

    @abstractmethod
    def snapshot(self) -> dict: ...
    # {"url": str, "elements": [{"selector": str?, "text": str?, "value": str?}]}

    @abstractmethod
    def fill(self, selector: str, value: str) -> None: ...

    @abstractmethod
    def click(self, selector: str | None = None, text: str | None = None) -> None: ...

    @abstractmethod
    def read_text(self, selector: str) -> str: ...


def resolve(value, ctx: dict):
    """Expand '$credentials.vendor.user' style references against the runtime context."""
    if isinstance(value, str) and value.startswith("$"):
        cur = ctx
        for part in value[1:].split("."):
            if not isinstance(cur, dict) or part not in cur:
                raise KeyError(f"unresolved reference: {value!r}")
            cur = cur[part]
        return cur
    return value


def run_flow(flow: Flow, driver: Driver, ctx: dict, approver=None, on_event=None) -> list[dict]:
    """Execute a flow. approver: callable(question: dict) -> bool.

    No approver means confirm steps and confirm-band pages are denied by default —
    fail closed, never forward.
    """
    events: list[dict] = []

    def emit(kind: str, **data) -> None:
        ev = {"event": kind, **data}
        events.append(ev)
        if on_event:
            on_event(ev)

    def finish(reason: str, **data) -> list[dict]:
        emit("FLOW_ABORTED", reason=reason, **data)
        return events

    driver.goto(flow.entry_url)
    executed_pages: set[str] = set()

    for _ in range(MAX_STEPS):
        snapshot = driver.snapshot()
        matched = best_page_match(flow, snapshot)
        if matched is None:
            emit("PAGE_UNRECOGNIZED", url=snapshot.get("url", ""))
            return finish("page_unrecognized", url=snapshot.get("url", ""))
        page, result = matched
        b = band(result.confidence, flow.thresholds)
        emit("PAGE_MATCHED", page=page.name, confidence=result.confidence, band=b, failed=result.failed)

        if b == ABORT:
            return finish("low_page_confidence", page=page.name)
        if page.name in executed_pages:
            return finish("page_loop", page=page.name)
        if b == CONFIRM:
            emit("PAGE_CONFIRM_REQUIRED", page=page.name, confidence=result.confidence)
            ok = bool(approver and approver({"kind": "page", "page": page.name, "confidence": result.confidence}))
            emit("PAGE_CONFIRM_RESULT", approved=ok)
            if not ok:
                return finish("page_confirmation_denied", page=page.name)

        executed_pages.add(page.name)
        for step in page.steps:
            status = _exec_step(step, driver, ctx, emit, approver)
            if status is not None:  # flow ended (complete or aborted)
                return events
        # steps done; next loop iteration snapshots whatever page resulted

    return finish("max_steps_exceeded")


def _exec_step(step: Step, driver: Driver, ctx: dict, emit, approver) -> bool | None:
    """Returns None to continue, True on complete, False when the flow aborted."""
    action, p = step.action, step.params

    if action == "fill":
        driver.fill(p["selector"], resolve(p["value"], ctx))
    elif action == "click":
        driver.click(selector=p.get("selector"), text=p.get("text"))
    elif action == "read":
        ctx[p["as"]] = driver.read_text(p["selector"])
        emit("READ", key=p["as"], value=str(ctx[p["as"]]))
    elif action == "wait":
        pass  # real driver waits for page stability; fixtures are instant
    elif action == "gate":
        ok, detail = evaluate_gate(p, ctx)
        if ok:
            emit("GATE_PASSED", gate=p.get("type"), detail=detail)
        else:
            emit("GATE_FAILED", gate=p.get("type"), detail=detail)
            emit("FLOW_ABORTED", reason="gate_failed")
            return False
    elif action == "confirm":
        emit("APPROVAL_REQUIRED", **p)
        approved = bool(approver and approver({"kind": "approval", **p}))
        emit("APPROVAL_RESULT", approved=approved)
        if not approved:
            emit("FLOW_ABORTED", reason="approval_denied")
            return False
    elif action == "complete":
        emit("FLOW_COMPLETE")
        return True
    else:
        emit("FLOW_ABORTED", reason=f"unknown_action:{action}")
        return False
    return None
