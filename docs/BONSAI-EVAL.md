# M2 — Bonsai model evaluation harness (spec)

Blocked on: Mac mini. This document is the complete spec so the Mac work
starts with a defined protocol, not exploration. Everything here is what the
Swift side must implement and measure.

## Why this exists

No published benchmarks exist for any Bonsai model on any iPhone. The vendor
quotes M5 Max (47 tok/s) and M4 desktop (12.7 tok/s) for the 27B; nothing for
the 8B/4B on a phone. The entire product rests on numbers nobody has measured.
This harness produces them.

## What runs

| Model | Device | Why |
|---|---|---|
| Ternary Bonsai 8B | iPhone 16 Plus (A18, 8GB) | the guinea-pig tier |
| Ternary Bonsai 4B | iPhone 16 Plus (as proxy for parents' 6GB tier) | the ship tier |
| Ternary Bonsai 4B | parents' phone (when upgraded) | the real target |

Runtime: PrismML mlx-swift fork (github.com/PrismML-Eng/mlx-swift), loaded
via the `LLMRuntime` module (ios/README.md). Model files are gitignored;
download from HF at bench time.

## Measurements (all required, none optional)

1. **Decode throughput** — tokens/sec over 128 generated tokens, batch 1,
   after warmup. Report median of 5 runs.
2. **Prompt processing** — tokens/sec over a 512-token prompt. Agent loops
   are prefill-bound; this number decides whether flows feel instant or sluggish.
3. **Time to first token** — cold model load to first output token. The
   handoff doc warned of 5–10s loads; on a phone this is the "is it alive" number.
4. **Peak memory** — jetsam pressure during load and during a 4K-context
   generation. If the OS kills the app, nothing else matters.
5. **Thermal curve** — tok/s sampled every 30s for 5 minutes of continuous
   generation. The handoff doc flagged throttling after ~5 min; bill-pay
   flows are short, but "read my mail" sessions are not.
6. **Tool-calling conformance** — the model must emit valid OpenAI-style
   `tool_calls` for the 10-skill registry. Measure: % of 50 scripted prompts
   that produce a parseable, in-registry call. Gate: >= 0.90 or the model
   cannot drive the flow engine and the tier drops.

## Gates (decide the ship tier)

| Metric | 8B on 16 Plus | 4B on 6GB tier |
|---|---|---|
| Decode | >= 15 tok/s | >= 12 tok/s |
| TTFT | <= 8 s | <= 6 s |
| Peak memory | no jetsam kill | no jetsam kill |
| Thermal | >= 80% of cold tok/s at minute 5 | same |
| Tool-call conformance | >= 0.90 | >= 0.90 |

If the 8B passes on the 16 Plus, it's the dev model. If the 4B fails any gate
on the 6GB tier, the parents' experience degrades to voice-chat-only with
flows driven by the decision layer — that is a scope change, record it in
DECISIONS.md.

## The interface the model must satisfy

`LLMRuntime` exposes exactly three operations; the model is swappable behind
them. Any model that can't satisfy all three is not a candidate.

```
generate(prompt, max_tokens) -> stream of tokens     # conversation, read-back
tool_call(prompt, registry)  -> typed tool call       # drives the flow engine
embed(text)                  -> vector (optional)     # memory retrieval, if used
```

## What this harness is NOT

- Not a fine-tune. Bonsai ships as-is; we evaluate, we don't train it.
- Not a benchmark for its own sake. Every number maps to a product decision:
  which tier ships, whether flows feel instant, whether the 8B is worth the
  memory pressure over the 4B.
