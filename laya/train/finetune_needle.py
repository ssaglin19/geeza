#!/usr/bin/env python3
"""
Fine-tune Needle on the intent-routing corpus.

Needle uses LoRA adapters on a ladder architecture (2-20 layers). We fine-tune
a small subnetwork (8 layers) on our 7-class intent corpus, then export to
.cact format for on-device deployment.

Usage:
  python finetune_needle.py --corpus ../datasets/intent_corpus.jsonl --epochs 10 --layers 8 --out needle_intent.cact
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Find the needle CLI
NEEDLE_CLI = Path(sys.executable).parent / "Scripts" / "needle.exe"
if not NEEDLE_CLI.exists():
    NEEDLE_CLI = "needle"  # fallback to PATH


def convert_corpus_to_needle_format(corpus_path: str, output_path: str):
    """Convert our JSONL corpus to Needle's training format."""
    records = []
    with open(corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            # Needle format: {"query": "...", "tool": "...", "args": {...}}
            records.append({
                "query": r["text"],
                "tool": r["label"],
                "args": {"query": r["text"]},
            })

    with open(output_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    return len(records)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, help="Input JSONL corpus")
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--layers", type=int, default=8, help="Subnetwork depth (2-20)")
    ap.add_argument("--out", default="needle_intent.cact", help="Output .cact file")
    ap.add_argument("--adapter", default="adapter.safetensors", help="LoRA adapter output")
    args = ap.parse_args()

    # Convert corpus
    needle_data = args.corpus.replace(".jsonl", "_needle.jsonl")
    print(f"Converting corpus to Needle format: {needle_data}")
    n = convert_corpus_to_needle_format(args.corpus, needle_data)
    print(f"  {n} examples")

    # Fine-tune
    print(f"Fine-tuning Needle ({args.layers} layers, {args.epochs} epochs) ...")
    train_cmd = [
        str(NEEDLE_CLI), "finetune", needle_data,
        "--epochs", str(args.epochs),
        "--out", args.adapter,
    ]
    print(f"  Command: {' '.join(train_cmd)}")

    result = subprocess.run(train_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Error: {result.stderr}")
        sys.exit(1)
    print(f"  Adapter saved: {args.adapter}")

    # Build .cact
    print(f"Building .cact ({args.layers} layers) ...")
    build_cmd = [
        str(NEEDLE_CLI), "build",
        "--lora", args.adapter,
        "--layers", str(args.layers),
        "--out", args.out,
    ]
    print(f"  Command: {' '.join(build_cmd)}")

    result = subprocess.run(build_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Error: {result.stderr}")
        sys.exit(1)
    print(f"  Model saved: {args.out}")

    # Evaluate
    print("\nEvaluating ...")
    eval_cmd = [
        sys.executable, "eval_needle.py",
        "--corpus", args.corpus,
        "--model", args.out,
        "--n", "100",
    ]
    print(f"  Command: {' '.join(eval_cmd)}")

    result = subprocess.run(eval_cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"  Warnings: {result.stderr}")


if __name__ == "__main__":
    main()
