#!/usr/bin/env python3
"""
Generate the intent-routing training corpus for the Laya fine-tune.

Maps natural-language voice commands (as an elderly person would say them)
to the 10 skills the assistant can execute. The model learns: given a
transcribed utterance, which skill should handle it?

Skills (from laya/questions/intent-routing.json):
  pay_bill, check_calendar, read_email, call_family, medication_reminder,
  grocery_order, weather_check, scam_check, general_question, emergency

Output: JSONL, one record per line:
  {"text": "...", "label": "<skill>", "category": "<skill>", "source": "synthetic"}

usage: python generate_intent_corpus.py --out intent_corpus.jsonl [--n-per-skill 200] [--seed 42]
"""
import argparse
import json
import random

# ---------------------------------------------------------------------------
# Utterance templates per skill. Elderly speech patterns: polite, rambling,
# sometimes uncertain, often with filler. Templates include variations.
# Slots are lists of interchangeable phrases; the generator samples one.
# ---------------------------------------------------------------------------

FILLER_START = ["", "", "", "Um, ", "Well, ", "Oh, ", "Hey, ", "Listen, ", "Honey, "]
FILLER_END = ["", "", "", " please.", " if you can.", " thanks.", " okay?"]
UNCERTAIN = ["I think ", "maybe ", "I guess ", "", "", ""]

UTTERANCES = {
    "pay_bill": [
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
    ],
    "check_calendar": [
        "What's on my calendar {when}",
        "Do I have any appointments {when}",
        "What am I doing {when}",
        "Check my schedule for {when}",
        "Am I free {when}",
        "What's coming up {when}",
        "Do I have anything {when}",
        "What does my day look like {when}",
        "Any doctor appointments {when}",
        "When is my next appointment",
    ],
    "read_email": [
        "Read my email",
        "Do I have any new emails",
        "Check my inbox",
        "Any messages for me",
        "Read me my mail",
        "What's in my email",
        "Did anyone email me",
        "Check if {person} emailed me",
        "Read the email from {person}",
        "I want to hear my messages",
    ],
    "call_family": [
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
    ],
    "medication_reminder": [
        "Did I take my {med} {when}",
        "Remind me to take my {med}",
        "It's time for my pills",
        "Set a reminder for my {med}",
        "What medications do I take {when}",
        "I need to take my {med} at {time}",
        "Don't let me forget my {med}",
        "When do I take my {med}",
        "My pill schedule",
        "Am I supposed to take something {when}",
    ],
    "grocery_order": [
        "I need groceries",
        "Order some {item} for me",
        "Can you get me {item} from the store",
        "We're out of {item}",
        "Add {item} to my grocery list",
        "I need to order food",
        "Get me some {item}",
        "Order groceries from {store}",
        "I need {item} and {item2}",
        "Can you do the shopping",
    ],
    "weather_check": [
        "What's the weather like",
        "Is it going to rain {when}",
        "How cold is it outside",
        "What's the temperature",
        "Do I need a jacket {when}",
        "Weather forecast for {when}",
        "Is it nice out",
        "Will it snow {when}",
        "How hot is it going to get",
        "Should I bring an umbrella",
    ],
    "scam_check": [
        "Is this email a scam",
        "I got a strange message, can you check it",
        "Someone called saying they're from {org}, is that real",
        "This doesn't look right, is it fraud",
        "Check if this is a scam",
        "I think someone is trying to trick me",
        "Is this phone call legitimate",
        "Can you look at this email and tell me if it's safe",
        "I got a text about {topic}, is it real",
        "Something seems fishy about this",
    ],
    "general_question": [
        "What time is it",
        "What's {number} plus {number2}",
        "How do you spell {word}",
        "What's the date {when}",
        "Who is {person}",
        "What does {word} mean",
        "How many {unit} in a {unit2}",
        "Tell me about {topic}",
        "What year did {event} happen",
        "How do I {task}",
    ],
    "emergency": [
        "I need help",
        "Call 911",
        "I fell and I can't get up",
        "Something is wrong, get help",
        "I'm having chest pain",
        "I can't breathe",
        "Emergency, please help",
        "I think I'm having a stroke",
        "Someone broke into my house",
        "I smell gas",
    ],
}

# Slot values
BILLS = ["electric", "gas", "water", "phone", "internet", "cable", "insurance"]
COMPANIES = ["Consumers Energy", "DTE", "Comcast", "AT&T", "Verizon", "the water company"]
PEOPLE = ["Sean", "Sarah", "Mike", "Jenny", "David", "Lisa", "Tom", "Mary"]
RELATIONS = ["son", "daughter", "grandson", "granddaughter", "sister", "brother"]
MEDS = ["blood pressure pill", "cholesterol medication", "vitamin D", "metformin",
        "Lisinopril", "atorvastatin", "levothyroxine", "aspirin"]
WHEN = ["today", "tomorrow", "this week", "next week", "this morning", "this afternoon"]
TIMES = ["8 AM", "noon", "6 PM", "bedtime", "breakfast", "dinner"]
ITEMS = ["milk", "bread", "eggs", "bananas", "chicken", "rice", "coffee", "toilet paper"]
STORES = ["Kroger", "Meijer", "Walmart", "Costco", "the store"]
ORGS = ["Medicare", "the IRS", "Social Security", "my bank", "Microsoft", "Apple"]
TOPICS = ["a package", "my account", "a refund", "my computer", "my insurance"]
NUMBERS = ["five", "twelve", "twenty-three", "forty", "a hundred"]
WORDS = ["necessary", "restaurant", "Wednesday", "February", "receipt"]
UNITS = ["ounces", "inches", "tablespoons", "feet"]
UNITS2 = ["pound", "foot", "cup", "yard"]
EVENTS = ["the war end", "man land on the moon", "the Berlin Wall fall"]
TASKS = ["reset my password", "turn off the Wi-Fi", "print something", "zoom in"]


def fill(template: str, rng: random.Random) -> str:
    text = template
    slots = {
        "bill": rng.choice(BILLS),
        "company": rng.choice(COMPANIES),
        "person": rng.choice(PEOPLE),
        "relation": rng.choice(RELATIONS),
        "med": rng.choice(MEDS),
        "when": rng.choice(WHEN),
        "time": rng.choice(TIMES),
        "item": rng.choice(ITEMS),
        "item2": rng.choice(ITEMS),
        "store": rng.choice(STORES),
        "org": rng.choice(ORGS),
        "topic": rng.choice(TOPICS),
        "number": rng.choice(NUMBERS),
        "number2": rng.choice(NUMBERS),
        "word": rng.choice(WORDS),
        "unit": rng.choice(UNITS),
        "unit2": rng.choice(UNITS2),
        "event": rng.choice(EVENTS),
        "task": rng.choice(TASKS),
    }
    for key, value in slots.items():
        text = text.replace("{" + key + "}", value, 1)
    return text


def add_elderly_speech_patterns(text: str, rng: random.Random) -> str:
    """Add realistic speech patterns: fillers, uncertainty, politeness."""
    start = rng.choice(FILLER_START)
    end = rng.choice(FILLER_END)
    uncertain = rng.choice(UNCERTAIN)

    # Sometimes lowercase (transcription artifacts)
    if rng.random() < 0.3:
        text = text[0].lower() + text[1:] if text else text

    # Sometimes add uncertainty
    if uncertain and rng.random() < 0.4:
        # Insert after first few words
        words = text.split()
        if len(words) > 2:
            insert_at = rng.randint(1, min(3, len(words) - 1))
            words.insert(insert_at, uncertain.strip())
            text = " ".join(words)

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
    ap.add_argument("--out", default="intent_corpus.jsonl")
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
