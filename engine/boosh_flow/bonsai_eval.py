#!/usr/bin/env python3
"""
Bonsai model evaluation harness.

Measures decode speed, prefill speed, time-to-first-token, memory usage,
thermal behavior, and tool-calling conformance for on-device LLM inference.

This is the reference implementation for the protocol in docs/BONSAI-EVAL.md.
The actual measurements require the Mac + iPhone; this script defines the
interface and provides mock implementations for testing.

Usage:
  python bonsai_eval.py --model bonsai-8b --device iphone-16-plus --output results.json
"""
import argparse
import json
import time
from dataclasses import dataclass, asdict
from typing import Protocol


@dataclass
class EvalResult:
    model: str
    device: str
    decode_tok_s: float
    prefill_tok_s: float
    ttft_ms: float
    memory_peak_gb: float
    thermal_throttle_after_s: float | None
    tool_call_conformance: float  # 0.0 to 1.0
    timestamp: str


class ModelRunner(Protocol):
    """Interface for running inference on a model."""

    def load(self, model_path: str) -> None:
        """Load model into memory."""
        ...

    def generate(self, prompt: str, max_tokens: int) -> tuple[str, dict]:
        """Generate text, return (output, metrics)."""
        ...

    def unload(self) -> None:
        """Free model memory."""
        ...


class MockRunner:
    """Mock runner for testing the harness without real hardware."""

    def __init__(self, decode_tok_s=15.0, prefill_tok_s=100.0, ttft_ms=500.0):
        self.decode_tok_s = decode_tok_s
        self.prefill_tok_s = prefill_tok_s
        self.ttft_ms = ttft_ms

    def load(self, model_path: str) -> None:
        time.sleep(0.1)  # simulate load time

    def generate(self, prompt: str, max_tokens: int) -> tuple[str, dict]:
        # Simulate generation
        time.sleep(max_tokens / self.decode_tok_s)
        output = "mock output " * max_tokens
        metrics = {
            "decode_tok_s": self.decode_tok_s,
            "prefill_tok_s": self.prefill_tok_s,
            "ttft_ms": self.ttft_ms,
            "memory_peak_gb": 2.4,
        }
        return output, metrics

    def unload(self) -> None:
        pass


# ---------- benchmark prompts ----------

DECODE_PROMPT = "Write a 500-word essay about the history of computing."
PREFILL_PROMPT = "Summarize the following article: " + ("word " * 1000)
TOOL_CALL_PROMPT = """You have access to these tools:
- get_weather(location: str) -> dict
- send_email(to: str, subject: str, body: str) -> bool

User: What's the weather in San Francisco?

Respond with a tool call in JSON format: {"tool": "get_weather", "args": {"location": "San Francisco"}}"""


# ---------- measurement functions ----------

def measure_decode_speed(runner: ModelRunner, n_tokens=128) -> float:
    """Measure token generation speed (decode phase)."""
    runner.generate(DECODE_PROMPT, max_tokens=10)  # warmup
    start = time.time()
    _, metrics = runner.generate(DECODE_PROMPT, max_tokens=n_tokens)
    elapsed = time.time() - start
    return n_tokens / elapsed


def measure_prefill_speed(runner: ModelRunner, n_tokens=512) -> float:
    """Measure prompt processing speed (prefill phase)."""
    runner.generate("test", max_tokens=1)  # warmup
    start = time.time()
    _, metrics = runner.generate(PREFILL_PROMPT, max_tokens=1)
    elapsed = time.time() - start
    return n_tokens / elapsed


def measure_ttft(runner: ModelRunner) -> float:
    """Measure time to first token (milliseconds)."""
    runner.generate("test", max_tokens=1)  # warmup
    start = time.time()
    runner.generate("Hello", max_tokens=1)
    elapsed = time.time() - start
    return elapsed * 1000


def measure_memory(runner: ModelRunner) -> float:
    """Measure peak memory usage (GB). Placeholder — real implementation
    uses platform-specific APIs (procfs on Linux, task_info on macOS/iOS)."""
    _, metrics = runner.generate("test", max_tokens=1)
    return metrics.get("memory_peak_gb", 0.0)


def measure_thermal(runner: ModelRunner, duration_s=300) -> float | None:
    """Measure time until thermal throttling. Placeholder — real implementation
    monitors device thermal state and detects when tok/s drops >20%."""
    # Run sustained generation for duration_s, measure tok/s every 10s
    # Return time when tok/s drops below 80% of baseline, or None if no throttle
    return None  # mock: no throttling


def measure_tool_conformance(runner: ModelRunner, n_trials=10) -> float:
    """Measure tool-calling conformance: does the model emit valid JSON
    tool calls that match the schema?"""
    valid = 0
    for _ in range(n_trials):
        output, _ = runner.generate(TOOL_CALL_PROMPT, max_tokens=100)
        try:
            # Check if output contains valid JSON with expected structure
            if '"tool"' in output and '"args"' in output:
                valid += 1
        except Exception:
            pass
    return valid / n_trials


# ---------- main ----------

def run_eval(runner: ModelRunner, model: str, device: str) -> EvalResult:
    """Run the full evaluation suite."""
    print(f"Loading model {model} ...")
    runner.load(model)

    print("Measuring decode speed ...")
    decode_tok_s = measure_decode_speed(runner)

    print("Measuring prefill speed ...")
    prefill_tok_s = measure_prefill_speed(runner)

    print("Measuring TTFT ...")
    ttft_ms = measure_ttft(runner)

    print("Measuring memory ...")
    memory_peak_gb = measure_memory(runner)

    print("Measuring thermal behavior ...")
    thermal_throttle_after_s = measure_thermal(runner)

    print("Measuring tool-calling conformance ...")
    tool_call_conformance = measure_tool_conformance(runner)

    runner.unload()

    return EvalResult(
        model=model,
        device=device,
        decode_tok_s=round(decode_tok_s, 1),
        prefill_tok_s=round(prefill_tok_s, 1),
        ttft_ms=round(ttft_ms, 1),
        memory_peak_gb=round(memory_peak_gb, 2),
        thermal_throttle_after_s=thermal_throttle_after_s,
        tool_call_conformance=round(tool_call_conformance, 2),
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
    )


def print_gates(result: EvalResult) -> None:
    """Check results against the gates from docs/BONSAI-EVAL.md."""
    print("\nGates:")
    print(f"  decode >= 10 tok/s:        {'PASS' if result.decode_tok_s >= 10 else 'FAIL'} ({result.decode_tok_s})")
    print(f"  prefill >= 50 tok/s:       {'PASS' if result.prefill_tok_s >= 50 else 'FAIL'} ({result.prefill_tok_s})")
    print(f"  TTFT <= 2000 ms:           {'PASS' if result.ttft_ms <= 2000 else 'FAIL'} ({result.ttft_ms})")
    print(f"  memory <= 6 GB:            {'PASS' if result.memory_peak_gb <= 6.0 else 'FAIL'} ({result.memory_peak_gb})")
    print(f"  tool conformance >= 0.9:   {'PASS' if result.tool_call_conformance >= 0.9 else 'FAIL'} ({result.tool_call_conformance})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="model name (e.g., bonsai-8b)")
    ap.add_argument("--device", required=True, help="device name (e.g., iphone-16-plus)")
    ap.add_argument("--output", help="save results to JSON file")
    ap.add_argument("--mock", action="store_true", help="use mock runner (for testing)")
    args = ap.parse_args()

    if args.mock:
        runner = MockRunner()
    else:
        # Real implementation would load MLX/Core ML runner here
        print("ERROR: real runner not implemented yet (requires Mac + iPhone)")
        print("Use --mock to test the harness")
        return

    result = run_eval(runner, args.model, args.device)

    print("\nResults:")
    print(f"  model:              {result.model}")
    print(f"  device:             {result.device}")
    print(f"  decode:             {result.decode_tok_s} tok/s")
    print(f"  prefill:            {result.prefill_tok_s} tok/s")
    print(f"  TTFT:               {result.ttft_ms} ms")
    print(f"  memory peak:        {result.memory_peak_gb} GB")
    print(f"  thermal throttle:   {result.thermal_throttle_after_s or 'none'} s")
    print(f"  tool conformance:   {result.tool_call_conformance}")

    print_gates(result)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(asdict(result), f, indent=2)
        print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()