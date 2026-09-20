#!/usr/bin/env python3
"""
Evaluate Needle on the intent-routing corpus with improved tool descriptions.

The base model confused emergency with check_safety because both involve
"danger." The fix: action-oriented descriptions that emphasize WHAT the tool
does, not the topic it covers.

Usage:
  python eval_needle_v2.py --corpus ../datasets/intent_corpus.jsonl --n 100
"""

import argparse
import json
import sys
from collections import defaultdict

import needle


# Improved tool descriptions: action-oriented, distinctive, unambiguous
@needle.tool
def handle_bills(query: str):
    """Pay a utility bill, credit card, or invoice. Handle account payments."""
    return {"skill": "handle_bills", "query": query}


@needle.tool
def check_schedule(query: str):
    """Look up calendar appointments, medication times, or daily schedule."""
    return {"skill": "check_schedule", "query": query}


@needle.tool
def contact_family(query: str):
    """Call, text, or read messages from family members."""
    return {"skill": "contact_family", "query": query}


@needle.tool
def get_groceries(query: str):
    """Order food, household items, or prescription refills from a store."""
    return {"skill": "get_groceries", "query": query}


@needle.tool
def check_safety(query: str):
    """Verify if an email, phone call, or text message is a scam or fraud."""
    return {"skill": "check_safety", "query": query}


@needle.tool
def general_help(query: str):
    """Answer questions, tell time, do math, explain concepts, or look up facts."""
    return {"skill": "general_help", "query": query}


@needle.tool
def emergency(query: str):
    """Call 911, request ambulance, report fire, or get immediate police help."""
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


def load_corpus(path, n=None):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    if n and len(records) > n:
        # Stratified sample
        by_label = defaultdict(list)
        for r in records:
            by_label[r["label"]].append(r)
        per_label = n // len(by_label)
        records = []
        for label, recs in by_label.items():
            records.extend(recs[:per_label])
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--n", type=int, default=100, help="Examples to evaluate")
    args = ap.parse_args()

    print(f"Loading corpus: {args.corpus}")
    records = load_corpus(args.corpus, n=args.n)
    print(f"  {len(records)} examples")

    print("Loading Needle ...")
    agent = needle.Needle(tools=TOOLS)

    correct = 0
    total = 0
    by_label = defaultdict(lambda: {"correct": 0, "total": 0})
    confusion = defaultdict(list)

    print(f"\nEvaluating {len(records)} examples ...")
    for i, r in enumerate(records):
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{len(records)} ...")

        text = r["text"]
        expected = r["label"]

        result = agent.run(text)
        results = result.get("results", [])

        if not results:
            predicted = "none"
        else:
            first = results[0]
            predicted = first.get("skill", "unknown") if isinstance(first, dict) else "unknown"

        is_correct = predicted == expected
        correct += is_correct
        total += 1
        by_label[expected]["correct"] += is_correct
        by_label[expected]["total"] += 1

        if not is_correct:
            confusion[expected].append(predicted)

    accuracy = correct / total if total else 0.0

    print(f"\nResults:")
    print(f"  Accuracy: {accuracy:.3f} ({correct}/{total})")

    print(f"\n  Per-class recall:")
    for label in sorted(by_label.keys()):
        c = by_label[label]["correct"]
        t = by_label[label]["total"]
        recall = c / t if t else 0.0
        print(f"    {label}: {c}/{t} = {recall:.2f}")

    if confusion:
        print(f"\n  Confusion (true -> predicted):")
        for true_label in sorted(confusion.keys()):
            preds = confusion[true_label]
            from collections import Counter
            counts = Counter(preds)
            for pred, count in counts.most_common(3):
                print(f"    {true_label} -> {pred} ({count}x)")

    # Gates
    print(f"\n  Gates:")
    print(f"    accuracy >= 0.70:  {'PASS' if accuracy >= 0.70 else 'FAIL'} ({accuracy:.3f})")
    print(f"    accuracy >= 0.80:  {'PASS' if accuracy >= 0.80 else 'FAIL'} ({accuracy:.3f})")


if __name__ == "__main__":
    main()
