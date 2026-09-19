# Flow engine — reference implementation

Deterministic System 0: loads flow definitions, matches pages by weighted
anchors behind a hard URL gate, routes on confidence bands, executes steps,
runs sanity gates, and freezes at the approval gate. Stdlib only, Python 3.10+.

This is the **spec the Swift port must reproduce exactly** — same flow JSON,
same band thresholds, same event stream. Port notes in `ios/README.md`.

## Run tests

From `engine/`:

```
python -m unittest discover -s tests -t . -v
```

## Modules

| File | Job |
|---|---|
| `schema.py` | dataclasses, JSON loading, static `validate_flow` (3+ anchors, confirm required when `spends`) |
| `match.py` | `page_confidence` — weighted anchors, URL hard gate; `best_page_match` |
| `router.py` | confidence bands: act / confirm / abort |
| `gates.py` | `amount_sanity` and friends; context path resolution |
| `engine.py` | `run_flow` executor, `Driver` abstraction, fail-closed approvals |

## Design rules baked into the code

- **Fail closed.** No approver → confirm steps are denied. Unknown gate type →
  fail. Unparseable amount → fail.
- **The approval gate is a step type**, not a policy the model can negotiate.
- **URL is a hard gate** — anchor matches alone can never identify a page.
- **Page loop guard** — the same page executing twice aborts (site drift).
- Every decision emits an event; the event stream is the trace log.
