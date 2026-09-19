# Flow schema v1 (JSON)

## Top level

| Key | Type | Required | Notes |
|---|---|---|---|
| `name` | string | ✓ | stable id, e.g. `consumers-energy-pay` |
| `vendor` | string | ✓ | display name |
| `version` | int | | bump when pages/steps change |
| `entry_url` | string | ✓ | where the flow starts |
| `spends` | bool | | if true, a `confirm` step is mandatory (load-time check) |
| `thresholds` | object | | `{"act": 0.85, "confirm": 0.5}` defaults |
| `pages` | array | ✓ | ordered page specs |

## Page spec

| Key | Type | Notes |
|---|---|---|
| `name` | string | unique within the flow |
| `match.url_host` | string | **hard gate**: snapshot host must equal this exactly |
| `match.url_contains` | string | path+query substring, checked after the host passes |
| `match.anchors` | array | 3+; each `{selector?, text?, weight}` — exactly one of selector/text |
| `steps` | array | executed in order once the page matches |

Confidence = sum(weights of hit anchors) / sum(all anchor weights). A page
whose host or path check fails scores 0 no matter the anchors — a phishing
lookalike can reproduce any DOM, but it cannot live on the real domain.

## Step types

| Action | Params | Meaning |
|---|---|---|
| `fill` | `selector`, `value` | value may be `$ctx.path` reference (credentials, read values) |
| `click` | `selector` or `text` | one of the two |
| `read` | `selector`, `as` | captures element text into `ctx[as]` |
| `wait` | `ms` | reference engine: no-op; driver waits for stability |
| `gate` | see below | deterministic check; failure aborts the flow |
| `confirm` | `prompt`, extras | **approval gate** — flow freezes until the human taps |
| `complete` | — | flow finished successfully |

## Gates

| Type | Params | Logic |
|---|---|---|
| `amount_sanity` | `value_key`, `last_key`, `within_pct` | parsed amounts; fail if deviation from baseline exceeds pct, or either is unparseable |

Gate keys are paths into the runtime context (`ctx`): flow-read values (`as`),
`credentials.*` (keychain, injected by driver), `history.*` (persisted per
vendor by the app — e.g. last paid amount).

## Events (trace log)

`PAGE_MATCHED` (page, confidence, band, failed anchors), `PAGE_UNRECOGNIZED`,
`PAGE_CONFIRM_REQUIRED/RESULT`, `GATE_PASSED/FAILED`, `APPROVAL_REQUIRED/RESULT`,
`FLOW_COMPLETE`, `FLOW_ABORTED` (reason). Every event is logged locally;
the trace log is the audit trail for the caregiver.
