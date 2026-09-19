# Flow definitions

A flow is a registered vendor task: "pay the Consumers Energy bill." Flows are
**data** (JSON), not code — the same file drives the Python reference engine and
the Swift port. Authoring rules keep them deterministic and auditable.

See `schema.md` for the full format and `examples/` for a working flow.

## Rules

1. **Three or more anchors per page.** Page match confidence = matched anchor
   weight / total anchor weight. One anchor is a coincidence, three is a page.
2. **`url_host` is the hard gate.** Page must be on the exact registered
   domain — a lookalike site can copy any DOM but cannot live on the real
   host. `url_contains` is checked against the path+query only, after the host.
   Anchors alone never identify a page.
3. **Every flow that moves money or sends anything must contain a `confirm`
   step.** The engine does not enforce this at runtime — `validate_flow` flags
   it at load time and the app refuses to register the flow.
4. **Gates run before approval.** Sanity checks (amount within X% of baseline)
   happen in code before the human is asked to approve.
5. **No model output is a step.** Steps are fill / click / read / wait / gate /
   confirm / complete. Models assist reading (System 2) and page-recognition
   (System 1); they never produce step instructions.
6. **Credentials never appear in flow files.** `$credentials.vendor.password`
   is resolved from the keychain at runtime by the driver, not stored here.
