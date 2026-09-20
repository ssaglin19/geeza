#!/usr/bin/env python3
"""
Evaluate Needle for intent routing: given a user utterance, which skill
should handle it? Uses Needle's tool-calling interface where each skill
is a tool.

Usage:
  python eval_needle.py --corpus ../datasets/intent_corpus.jsonl --n 200
"""

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

# Needle imports
try:
    import needle
except ImportError:
    print("needle not installed. Run: pip install cactus-needle")
    sys.exit(1)


# Define the 7 skills as Needle tools
SKILLS = {
    "handle_bills": "Pay bills, handle utility payments, manage accounts with companies like Consumers Energy, DTE, Comcast",
    "check_schedule": "Check calendar, appointments, medication reminders, daily schedule",
    "contact_family": "Call family members, read messages from family, check if someone emailed or called",
    "get_groceries": "Order groceries, buy food items, shopping list, store pickup or delivery",
    "check_safety": "Check if something is a scam, fraud, phishing, or verify legitimacy of calls/emails",
    "general_help": "Answer general questions, tell time, do math, explain things, help with tasks",
    "emergency": "Emergency situations, call 911, medical emergency, fire, break-in, immediate danger",
}


@needle.tool
def handle_bills(query: str):
    """Pay bills, handle utility payments, manage accounts with companies."""
    return {"skill": "handle_bills", "query": query}


@needle.tool
def check_schedule(query: str):
    """Check calendar, appointments, medication reminders, daily schedule."""
    return {"skill": "check_schedule", "query": query}


@needle.tool
def contact_family(query: str):
    """Call family members, read messages from family, check communications."""
    return {"skill": "contact_family", "query": query}


@needle.tool
def get_groceries(query: str):
    """Order groceries, buy food items, manage shopping list."""
    return {"skill": "get_groceries", "query": query}


@needle.tool
def check_safety(query: str):
    """Check if something is a scam, fraud, or verify legitimacy."""
    return {"skill": "check_safety", "query": query}


@needle.tool
def general_help(query: str):
    """Answer general questions, tell time, do math, explain things."""
    return {"skill": "general_help", "query": query}


@needle.tool
def emergency(query: str):
    """Emergency situations, call 911, immediate danger."""
    return {"skill": "emergency", "query": query}


TOOLS = [
    handle_bills,
    check_schedule,
    contact_family,
    get_groceries,
    check_safety,
    general_help,
    emergency,
]


def load_corpus(path, n=None, seed=42):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    rng = random.Random(seed)
    rng.shuffle(records)
    if n and len(records) > n:
        # stratified: keep label balance
        by_label = defaultdict(list)
        for r in records:
            by_label[r["label"]].append(r)
        per_label = n // len(by_label)
        records = []
        for label, recs in by_label.items():
            records.extend(recs[:per_label])
        rng.shuffle(records)
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--n", type=int, default=200, help="max examples to evaluate")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print(f"Loading corpus from {args.corpus} ...")
    records = load_corpus(args.corpus, n=args.n, seed=args.seed)
    print(f"  {len(records)} examples")

    print("Loading Needle ...")
    agent = needle.Needle(tools=TOOLS)

    print("Evaluating ...")
    correct = 0
    total = 0
    class_correct = defaultdict(int)
    class_total = defaultdict(int)
    confusions = []

    for r in records:
        text = r["text"]
        true_label = r["label"]

        result = agent.run(text)
        # Needle returns results directly, not function_calls
        results = result.get("results", [])
        if not results:
            predicted = "none"
        else:
            # The tool returns {"skill": "...", "query": "..."}
            predicted = results[0].get("skill", "unknown")

        is_correct = predicted == true_label
        if is_correct:
            correct += 1
            class_correct[true_label] += 1
        else:
            confusions.append((true_label, predicted, text[:60]))

        class_total[true_label] += 1
        total += 1

        if total % 50 == 0:
            print(f"  {total}/{len(records)} ...")

    accuracy = correct / total if total else 0.0
    print(f"\n  accuracy: {accuracy:.3f} ({correct}/{total})")

    print(f"\n  per-class recall:")
    for label in sorted(class_total.keys()):
        recall = class_correct[label] / class_total[label]
        print(f"    {label}: {class_correct[label]}/{class_total[label]} = {recall:.2f}")

    print(f"\n  confusions (true -> predicted):")
    for true, pred, text in confusions[:20]:  # show first 20
        print(f"    {true} -> {pred}: {text}...")
    if len(confusions) > 20:
        print(f"    ... and {len(confusions) - 20} more")

    # Gate: accuracy >= 0.8
    print(f"\n  gate:")
    print(f"    accuracy >= 0.80: {'PASS' if accuracy >= 0.8 else 'FAIL'} ({accuracy:.3f})")


if __name__ == "__main__":
    main()
