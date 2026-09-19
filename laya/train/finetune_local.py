#!/usr/bin/env python3
"""
Fine-tune Laya on the scam-screen corpus, locally on CPU.

This is a custom training loop because laya.Agent does not expose a fit()
method — it wraps a DecisionModel (encoder + classification heads) and we
train that directly with PyTorch.

Usage:
  python finetune_local.py --corpus ../datasets/scam_corpus.jsonl --epochs 2 --n 500
"""

import argparse
import json
import random
import sys
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ---------- data ----------

class ScamDataset(Dataset):
    def __init__(self, records, tokenizer, label_map, max_len=512):
        self.records = records
        self.tok = tokenizer
        self.label_map = label_map
        self.max_len = max_len

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        r = self.records[idx]
        text = r["text"]
        label = self.label_map[r["label"]]
        enc = self.tok(
            text,
            truncation=True,
            max_length=self.max_len,
            padding="max_length",
            return_tensors="pt",
        )
        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "label": torch.tensor(label, dtype=torch.long),
        }


def load_corpus(path, n=None, seed=42):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    rng = random.Random(seed)
    rng.shuffle(records)
    if n and len(records) > n:
        # stratified: keep label balance
        from collections import defaultdict
        by_label = defaultdict(list)
        for r in records:
            by_label[r["label"]].append(r)
        per_label = n // len(by_label)
        records = []
        for label, recs in by_label.items():
            records.extend(recs[:per_label])
        rng.shuffle(records)
    return records


def split(records, seed=42):
    rng = random.Random(seed)
    from collections import defaultdict
    by_label = defaultdict(list)
    for r in records:
        by_label[r["label"]].append(r)
    for recs in by_label.values():
        rng.shuffle(recs)
    def cut(lst):
        n = len(lst)
        return lst[: int(n * 0.7)], lst[int(n * 0.7) : int(n * 0.85)], lst[int(n * 0.85) :]
    train, cal, ev = [], [], []
    for recs in by_label.values():
        tr, ca, ev_ = cut(recs)
        train.extend(tr)
        cal.extend(ca)
        ev.extend(ev_)
    return train, cal, ev


# ---------- metrics ----------

def expected_calibration_error(confs, corrects, n_bins=10):
    bins = [[] for _ in range(n_bins)]
    for c, ok in zip(confs, corrects):
        b = min(int(c * n_bins), n_bins - 1)
        bins[b].append((c, ok))
    ece = 0.0
    total = len(confs)
    for b in bins:
        if not b:
            continue
        avg_conf = sum(x[0] for x in b) / len(b)
        avg_acc = sum(x[1] for x in b) / len(b)
        ece += len(b) / total * abs(avg_conf - avg_acc)
    return ece


def evaluate_probs(probs, labels, threshold=0.5):
    preds = [1 if p >= threshold else 0 for p in probs]
    tp = sum(1 for p, l in zip(preds, labels) if p == 1 and l == 1)
    fp = sum(1 for p, l in zip(preds, labels) if p == 1 and l == 0)
    fn = sum(1 for p, l in zip(preds, labels) if p == 0 and l == 1)
    tn = sum(1 for p, l in zip(preds, labels) if p == 0 and l == 0)
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    acc = (tp + tn) / len(labels) if labels else 0.0
    return {"recall": recall, "fpr": fpr, "accuracy": acc, "tp": tp, "fp": fp, "fn": fn, "tn": tn}


# ---------- training ----------

def train_epoch(model, head, loader, optimizer, device):
    model.train()
    head.train()
    total_loss = 0.0
    criterion = nn.CrossEntropyLoss()
    for batch in loader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["label"].to(device)

        optimizer.zero_grad()
        # Get encoder output (CLS token representation)
        outputs = model.encoder(input_ids=input_ids, attention_mask=attention_mask)
        cls = outputs.last_hidden_state[:, 0, :]  # [CLS] token
        logits = head(cls)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(loader)


def predict_probs(model, head, records, tokenizer, device, max_len=512):
    model.eval()
    head.eval()
    probs = []
    with torch.no_grad():
        for r in records:
            enc = tokenizer(
                r["text"],
                truncation=True,
                max_length=max_len,
                padding="max_length",
                return_tensors="pt",
            )
            input_ids = enc["input_ids"].to(device)
            attention_mask = enc["attention_mask"].to(device)
            outputs = model.encoder(input_ids=input_ids, attention_mask=attention_mask)
            cls = outputs.last_hidden_state[:, 0, :]
            logits = head(cls)
            prob = torch.softmax(logits, dim=-1)[0, 1].item()  # P(scam)
            probs.append(prob)
    return probs


def predict_classes(model, head, records, tokenizer, device, max_len=512):
    model.eval()
    head.eval()
    preds = []
    with torch.no_grad():
        for r in records:
            enc = tokenizer(
                r["text"],
                truncation=True,
                max_length=max_len,
                padding="max_length",
                return_tensors="pt",
            )
            input_ids = enc["input_ids"].to(device)
            attention_mask = enc["attention_mask"].to(device)
            outputs = model.encoder(input_ids=input_ids, attention_mask=attention_mask)
            cls = outputs.last_hidden_state[:, 0, :]
            logits = head(cls)
            pred = torch.argmax(logits, dim=-1).item()
            preds.append(pred)
    return preds


def fit_temperature(probs, labels):
    """Find the temperature that minimizes log-loss on calibration data."""
    import math
    best_t, best_loss = 1.0, float("inf")
    for t100 in range(50, 301, 5):  # 0.5 to 3.0 in 0.05 steps
        t = t100 / 100.0
        loss = 0.0
        for p, y in zip(probs, labels):
            # apply temperature to logit
            p = max(min(p, 1 - 1e-7), 1e-7)
            logit = math.log(p / (1 - p))
            scaled = 1 / (1 + math.exp(-logit / t))
            scaled = max(min(scaled, 1 - 1e-7), 1e-7)
            loss -= y * math.log(scaled) + (1 - y) * math.log(1 - scaled)
        if loss < best_loss:
            best_loss = loss
            best_t = t
    return best_t


def apply_temperature(p, t):
    import math
    p = max(min(p, 1 - 1e-7), 1e-7)
    logit = math.log(p / (1 - p))
    return 1 / (1 + math.exp(-logit / t))


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--n", type=int, default=500, help="max examples to use")
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--save", default=None, help="save fine-tuned head to this path")
    ap.add_argument("--unfreeze", action="store_true",
                    help="also fine-tune the encoder (much slower, needs GPU for real runs)")
    ap.add_argument("--encoder-lr", type=float, default=1e-5,
                    help="learning rate for encoder when --unfreeze is set")
    ap.add_argument("--num-classes", type=int, default=2,
                    help="number of output classes (2 for binary scam/legit, 10 for intent routing)")
    args = ap.parse_args()

    print(f"Loading corpus from {args.corpus} ...")
    records = load_corpus(args.corpus, n=args.n, seed=args.seed)
    print(f"  {len(records)} examples")

    # Build label map from corpus
    labels = sorted(set(r["label"] for r in records))
    label_map = {label: idx for idx, label in enumerate(labels)}
    print(f"  classes: {label_map}")

    train, cal, ev = split(records, seed=args.seed)
    print(f"  split: {len(train)} train / {len(cal)} calibration / {len(ev)} eval")

    print("Loading Laya base model ...")
    import laya
    agent = laya.load("convaiinnovations/laya")
    model = agent.model
    tokenizer = agent.tok
    device = torch.device("cpu")
    model = model.to(device)

    # Build classification head on top of the encoder
    hidden_size = model.encoder.config.hidden_size
    head = nn.Sequential(
        nn.Linear(hidden_size, 256),
        nn.ReLU(),
        nn.Dropout(0.1),
        nn.Linear(256, args.num_classes),
    ).to(device)

    # Freeze encoder by default (faster, less overfitting on small data).
    # --unfreeze trains the encoder too; use a lower LR for it.
    if not args.unfreeze:
        for param in model.encoder.parameters():
            param.requires_grad = False

    train_ds = ScamDataset(train, tokenizer, label_map)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)

    if args.unfreeze:
        param_groups = [
            {"params": head.parameters(), "lr": args.lr},
            {"params": model.encoder.parameters(), "lr": args.encoder_lr},
        ]
        optimizer = torch.optim.AdamW(param_groups)
        print(f"Training head + encoder for {args.epochs} epochs "
              f"(head lr={args.lr}, encoder lr={args.encoder_lr}) ...")
    else:
        optimizer = torch.optim.AdamW(head.parameters(), lr=args.lr)
        print(f"Training head for {args.epochs} epochs (encoder frozen) ...")
    for epoch in range(args.epochs):
        loss = train_epoch(model, head, train_loader, optimizer, device)
        print(f"  epoch {epoch + 1}: loss = {loss:.4f}")

    # --- evaluate ---
    print("\nEvaluating ...")

    if args.num_classes == 2:
        # Binary classification (scam/legit)
        labels = [label_map[r["label"]] for r in ev]
        raw_probs = predict_probs(model, head, ev, tokenizer, device)

        # temperature fitting on calibration set
        cal_labels = [label_map[r["label"]] for r in cal]
        cal_probs = predict_probs(model, head, cal, tokenizer, device)
        temperature = fit_temperature(cal_probs, cal_labels)
        print(f"  fitted temperature: {temperature:.2f}")

        cal_probs_t = [apply_temperature(p, temperature) for p in cal_probs]
        ev_probs_t = [apply_temperature(p, temperature) for p in raw_probs]

        # metrics
        m = evaluate_probs(ev_probs_t, labels)
        confs = [max(p, 1 - p) for p in ev_probs_t]
        corrects = [1 if (p >= 0.5) == bool(l) else 0 for p, l in zip(ev_probs_t, labels)]
        ece = expected_calibration_error(confs, corrects)

        print(f"\n  eval metrics (temperature-scaled):")
        print(f"    recall (scam detected): {m['recall']:.3f}")
        print(f"    false positive rate:    {m['fpr']:.3f}")
        print(f"    accuracy:               {m['accuracy']:.3f}")
        print(f"    ECE:                    {ece:.3f}")

        # per-category recall
        from collections import defaultdict
        cat_probs = defaultdict(list)
        cat_labels = defaultdict(list)
        for r, p, l in zip(ev, ev_probs_t, labels):
            cat_probs[r["category"]].append(p)
            cat_labels[r["category"]].append(l)
        print(f"\n  per-category recall:")
        for cat in sorted(cat_probs.keys()):
            cps = cat_probs[cat]
            cls = cat_labels[cat]
            tp = sum(1 for p, l in zip(cps, cls) if p >= 0.5 and l == 1)
            fn = sum(1 for p, l in zip(cps, cls) if p < 0.5 and l == 1)
            total = tp + fn
            if total > 0:
                print(f"    {cat}: {tp}/{total} = {tp/total:.2f}")

        # gates
        print(f"\n  gates:")
        print(f"    recall >= 0.95:  {'PASS' if m['recall'] >= 0.95 else 'FAIL'} ({m['recall']:.3f})")
        print(f"    fpr <= 0.05:     {'PASS' if m['fpr'] <= 0.05 else 'FAIL'} ({m['fpr']:.3f})")
        print(f"    ece <= 0.10:     {'PASS' if ece <= 0.10 else 'FAIL'} ({ece:.3f})")

    else:
        # Multi-class classification (intent routing, mail triage)
        true_labels = [label_map[r["label"]] for r in ev]
        pred_labels = predict_classes(model, head, ev, tokenizer, device)

        # accuracy
        correct = sum(1 for t, p in zip(true_labels, pred_labels) if t == p)
        accuracy = correct / len(true_labels) if true_labels else 0.0
        print(f"\n  accuracy: {accuracy:.3f} ({correct}/{len(true_labels)})")

        # per-class recall
        from collections import defaultdict
        class_correct = defaultdict(int)
        class_total = defaultdict(int)
        for t, p in zip(true_labels, pred_labels):
            class_total[t] += 1
            if t == p:
                class_correct[t] += 1
        print(f"\n  per-class recall:")
        idx_to_label = {v: k for k, v in label_map.items()}
        for idx in sorted(class_total.keys()):
            label_name = idx_to_label[idx]
            recall = class_correct[idx] / class_total[idx]
            print(f"    {label_name}: {class_correct[idx]}/{class_total[idx]} = {recall:.2f}")

        # confusion matrix (compact)
        print(f"\n  confusion (true -> predicted):")
        for t, p in zip(true_labels, pred_labels):
            if t != p:
                print(f"    {idx_to_label[t]} -> {idx_to_label[p]}")

    if args.save:
        payload = {
            "head_state_dict": head.state_dict(),
            "hidden_size": hidden_size,
        }
        if args.num_classes == 2:
            payload["temperature"] = temperature
        if args.unfreeze:
            payload["encoder_state_dict"] = model.encoder.state_dict()
        torch.save(payload, args.save)
        print(f"\n  saved to {args.save}")


if __name__ == "__main__":
    main()
