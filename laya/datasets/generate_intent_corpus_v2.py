#!/usr/bin/env python3
"""
Generate the intent-routing training corpus, v2: 3 classes.

Merges the 7-class corpus into 3 classes that Laya can actually distinguish:
  - emergency: urgent help, 911, falls, medical emergencies
  - contact_family: call/text family, read messages from family
  - handle_bills: pay bills, check accounts, handle utilities

Everything else (schedule, groceries, weather, general questions) goes to
general_help, which is handled by keyword matching or the LLM directly.

Usage: python generate_intent_corpus_v2.py --out intent_corpus_v2.jsonl [--n-per-skill 200] [--seed 42]
"""
import argparse
import json
import random

# ---------------------------------------------------------------------------
# Utterance templates for the 3-class problem. More distinctive, action-oriented.
# ---------------------------------------------------------------------------

FILLER_START = ["", "", "", "Um, ", "Well, ", "Oh, ", "Hey, ", "Listen, ", "Honey, "]
FILLER_END = ["", "", "", " please.", " if you can.", " thanks.", " okay?"]

UTTERANCES = {
    "emergency": [
        "I need help right now",
        "Call 911",
        "I fell and I can't get up",
        "Something is wrong, get help",
        "I'm having chest pain",
        "I can't breathe",
        "Emergency, please help me",
        "I think I'm having a stroke",
        "Someone broke into my house",
        "I smell gas",
        "There's a fire",
        "I'm bleeding badly",
        "I need an ambulance",
        "My husband/wife is unresponsive",
        "I'm having a heart attack",
    ],
    "contact_family": [
        "Call {person}",
        "I want to talk to {person}",
        "Phone {person} for me",
        "Get {person} on the phone",
        "Can you call {person}",
        "I'd like to speak with {person}",
        "Ring {person}",
        "Dial {person}",
        "Call my {relation}",
        "I need to call {person} back",
        "Text {person} for me",
        "Send a message to {person}",
        "Did {person} call me",
        "Read the message from {person}",
        "Check if {person} texted",
    ],
    "handle_bills": [
        "I need to pay the {bill} bill",
        "Can you pay my {bill} bill for me",
        "The {bill} bill is due, can you take care of it",
        "I want to pay {company}",
        "Pay the {bill}",
        "My {bill} payment is due",
        "I got a bill from {company}, can you handle it",
        "Time to pay the {bill} again",
        "Take care of the {bill} bill",
        "I need to make a payment to {company}",
        "Check my {company} account balance",
        "How much do I owe {company}",
        "Did the {bill} bill come in",
        "Handle my {company} payment",
        "Set up autopay for {company}",
    ],
}

# Slot values
BILLS = ["electric", "gas", "water", "phone", "internet", "cable", "insurance"]
COMPANIES = ["Consumers Energy", "DTE", "Comcast", "AT&T", "Verizon", "the water company"]
PEOPLE = ["Sean", "Sarah", "Mike", "Jenny", "David", "Lisa", "Tom", "Mary"]
RELATIONS = ["son", "daughter", "grandson", "granddaughter", "sister", "brother"]


def fill(template: str, rng: random.Random) -> str:
    text = template
    slots = {
        "bill": rng.choice(BILLS),
        "company": rng.choice(COMPANIES),
        "person": rng.choice(PEOPLE),
        "relation": rng.choice(RELATIONS),
    }
    for key, value in slots.items():
        text = text.replace("{" + key + "}", value, 1)
    return text


def add_elderly_speech_patterns(text: str, rng: random.Random) -> str:
    start = rng.choice(FILLER_START)
    end = rng.choice(FILLER_END)
    if rng.random() < 0.3:
        text = text[0].lower() + text[1:] if text else text
    return f"{start}{text}{end}".strip()


def generate(skill: str, templates: list, n: int, rng: random.Random) -> list:
    records = []
    for _ in range(n):
        template = rng.choice(templates)
        text = fill(template, rng)
        text = add_elderly_speech_patterns(text, rng)
        records.append({
            "text": text,
            "label": skill,
            "category": skill,
            "source": "synthetic",
        })
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="intent_corpus_v2.jsonl")
    ap.add_argument("--n-per-skill", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    records = []
    for skill, templates in UTTERANCES.items():
        records.extend(generate(skill, templates, args.n_per_skill, rng))

    rng.shuffle(records)

    with open(args.out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} records to {args.out}")
    for skill in sorted(UTTERANCES.keys()):
        count = sum(1 for r in records if r["label"] == skill)
        print(f"  {skill}: {count}")


if __name__ == "__main__":
    main()
