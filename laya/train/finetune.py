#!/usr/bin/env python3
"""
Fine-tune Laya on the scam-screen corpus, temperature-fit, evaluate.

Designed to run on a free Colab/Kaggle T4. Expects the corpus JSONL from
generate_scam_corpus.py. Uses Laya's own training loop (pip install laya).

Gates (from laya/README.md M1):
  - scam recall >= 0.95
  - false-positive rate <= 0.05
  - ECE <= 0.10 after temperature fitting

usage:
  python finetune.py --corpus scam_corpus.jsonl --out ./laya-scam-v1
"""
import argparse
import json
import random
from pathlib import Path


def load_corpus(path: str):
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records


def split(records, seed=42):
    """80/10/10 train/cal/test, stratified by label."""
    rng = random.Random(seed)
    by_label = {"scam": [], "legit": []}
    for r in records:
        by_label[r["label"]].append(r)
    train, cal, test = [], [], []
    for label, group in by_label.items():
        rng.shuffle(group)
        n = len(group)
        train += group[: int(n * 0.8)]
        cal += group[int(n * 0.8): int(n * 0.9)]
        test += group[int(n * 0.9):]
    rng.shuffle(train)
    rng.shuffle(cal)
    rng.shuffle(test)
    return train, cal, test


def to_laya_examples(records):
    """Convert corpus records to Laya's training format for the scam-screen pack."""
    examples = []
    for r in records:
        examples.append({
            "state": {"text": r["text"]},
            "questions": {
                "is_scam": {
                    "type": "noul",
                    "instructions": "Is this message a scam, phishing attempt, or fraud?",
                    "target": 1.0 if r["label"] == "scam" else 0.0,
                },
            },
        })
    return examples


def evaluate(agent, records, threshold=0.5):
    """Return (recall, fpr, per-category recall) at the given noul threshold."""
    tp = fp = tn = fn = 0
    cat_totals, cat_hits = {}, {}
    for r in records:
        result = agent.predict({"text": r["text"]}, {
            "is_scam": {"type": "noul",
                        "instructions": "Is this message a scam, phishing attempt, or fraud?"}
        })
        p = result["answers"]["is_scam"]["noul"]
        pred = p >= threshold
        actual = r["label"] == "scam"
        if actual:
            cat_totals[r["category"]] = cat_totals.get(r["category"], 0) + 1
        if pred and actual:
            tp += 1
            cat_hits[r["category"]] = cat_hits.get(r["category"], 0) + 1
        elif pred and not actual:
            fp += 1
        elif not pred and actual:
            fn += 1
        else:
            tn += 1
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    per_cat = {c: cat_hits.get(c, 0) / t for c, t in sorted(cat_totals.items())}
    return recall, fpr, per_cat


def expected_calibration_error(agent, records, n_bins=10):
    """ECE over the is_scam noul probabilities."""
    bins = [[] for _ in range(n_bins)]
    for r in records:
        result = agent.predict({"text": r["text"]}, {
            "is_scam": {"type": "noul",
                        "instructions": "Is this message a scam, phishing attempt, or fraud?"}
        })
        p = result["answers"]["is_scam"]["noul"]
        actual = 1.0 if r["label"] == "scam" else 0.0
        b = min(int(p * n_bins), n_bins - 1)
        bins[b].append((p, actual))
    ece, n = 0.0, len(records)
    for b in bins:
        if not b:
            continue
        conf = sum(p for p, _ in b) / len(b)
        acc = sum(a for _, a in b) / len(b)
        ece += (len(b) / n) * abs(acc - conf)
    return ece


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", default="./laya-scam-v1")
    ap.add_argument("--base", default="convaiinnovations/laya")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    import laya  # noqa: deferred so --help works without the dep

    records = load_corpus(args.corpus)
    train, cal, test = split(records, args.seed)
    print(f"Split: {len(train)} train / {len(cal)} cal / {len(test)} test")

    # Fine-tune. Laya's API: load base, call .fit() with examples.
    agent = laya.load(args.base)
    agent.fit(to_laya_examples(train), epochs=args.epochs)

    # Temperature-fit on the calibration split.
    if hasattr(agent, "fit_temperature"):
        agent.fit_temperature(to_laya_examples(cal))
        print("Temperature fitted on calibration split")
    else:
        print("WARNING: agent has no fit_temperature; ECE gate may fail")

    # Evaluate on the held-out test split.
    recall, fpr, per_cat = evaluate(agent, test)
    ece = expected_calibration_error(agent, test)

    print("\n=== Test metrics ===")
    print(f"scam recall: {recall:.3f}  (gate: >= 0.95)")
    print(f"false-positive rate: {fpr:.3f}  (gate: <= 0.05)")
    print(f"ECE: {ece:.3f}  (gate: <= 0.10)")
    print("\nPer-category scam recall:")
    for cat, r in per_cat.items():
        flag = "" if r >= 0.90 else "  <-- BELOW 0.90"
        print(f"  {cat}: {r:.3f}{flag}")

    gates = [("recall", recall, 0.95, ">="), ("fpr", fpr, 0.05, "<="), ("ece", ece, 0.10, "<=")]
    failed = [name for name, v, g, op in gates if (v < g if op == ">=" else v > g)]
    if failed:
        print(f"\nGATES FAILED: {', '.join(failed)}. Do not ship this checkpoint.")
    else:
        print("\nAll gates passed.")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    agent.save(str(out))
    print(f"Checkpoint saved to {out}")


if __name__ == "__main__":
    main()
