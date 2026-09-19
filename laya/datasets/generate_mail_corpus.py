#!/usr/bin/env python3
"""
Generate the mail-triage training corpus for the Laya fine-tune.

Classifies emails into categories an elderly person cares about:
  bill, medical, personal, junk, scam

The model learns: given an email (subject + body), which category is it?
This drives the "read my mail" skill — it knows what to prioritize.

Output: JSONL, one record per line:
  {"text": "Subject: ...\n\n...", "label": "<category>", "category": "<category>", "source": "synthetic"}

usage: python generate_mail_corpus.py --out mail_corpus.jsonl [--n-per-category 300] [--seed 42]
"""
import argparse
import json
import random

# ---------------------------------------------------------------------------
# Email templates per category. Format: "Subject: ...\n\n<body>"
# Realistic sender names, subject lines, and body content.
# ---------------------------------------------------------------------------

NAMES = ["Dr. Patel", "Dr. Nguyen", "Dr. Kowalski", "Sarah", "Mike", "Jenny",
         "Pastor Dave", "Linda", "Ruth", "Tom", "Mary", "Bob"]
COMPANIES = ["Consumers Energy", "DTE Energy", "Comcast", "AT&T", "Verizon",
             "AARP", "Blue Cross Blue Shield", "Medicare", "Social Security"]
PHARMACIES = ["CVS Pharmacy", "Walgreens", "Kroger Pharmacy", "Meijer Pharmacy"]
STORES = ["Kroger", "Meijer", "Walmart", "Costco", "Target"]

EMAILS = {
    "bill": [
        ("Your {company} statement is ready",
         "Dear Customer,\n\nYour {company} bill for ${amount} is now available. "
         "Payment is due by {date}.\n\nView and pay your bill online at {company}.com.\n\n"
         "Thank you,\n{company} Customer Service"),
        ("Payment reminder: {company}",
         "This is a friendly reminder that your {company} payment of ${amount} "
         "is due on {date}.\n\nPay online or by phone at the number on your statement."),
        ("{company} AutoPay confirmation",
         "Your automatic payment of ${amount} to {company} will be processed on {date}. "
         "No action is required.\n\nTo make changes, log in to your account."),
        ("Your insurance premium is due",
         "Your {company} premium payment of ${amount} is due {date}. "
         "Pay online to avoid a lapse in coverage."),
    ],
    "medical": [
        ("Appointment reminder: {name}",
         "This is a reminder that you have an appointment with {name} on {date} at {time}.\n\n"
         "Location: {clinic}\nPlease arrive 15 minutes early.\n\n"
         "To reschedule, call our office."),
        ("Your prescription is ready",
         "Your prescription at {pharmacy} is ready for pickup.\n\n"
         "Pickup by: {date}\n\nQuestions? Call the pharmacy directly."),
        ("Test results available",
         "Your recent lab results are now available in your patient portal.\n\n"
         "Log in to view them, or wait for your doctor to contact you."),
        ("{pharmacy}: Refill reminder",
         "It's time to refill your prescription for {med}.\n\n"
         "Refill online or call {pharmacy}."),
        ("Annual wellness visit",
         "Medicare covers an annual wellness visit at no cost to you. "
         "Schedule yours with {name} by calling our office."),
    ],
    "personal": [
        ("Re: {topic}",
         "Hi Mom,\n\n{message}\n\nLove,\n{name}"),
        ("{topic}",
         "Hi Grandma,\n\n{message}\n\nSee you soon!\n{name}"),
        ("Sunday dinner",
         "Hi Mom,\n\nAre you still coming for dinner on Sunday? "
         "Let me know if you need a ride.\n\nLove,\n{name}"),
        ("Photos from {event}",
         "Hi!\n\nHere are the photos from {event}. You look great in them!\n\n"
         "Talk soon,\n{name}"),
        ("Checking in",
         "Hi Mom,\n\nJust checking to see how you're doing. "
         "Give me a call when you have a chance.\n\nLove,\n{name}"),
    ],
    "junk": [
        ("{percent}% off this weekend only!",
         "Don't miss our biggest sale of the season! "
         "Save {percent}% on everything at {store}.\n\nShop now!"),
        ("Your {store} rewards are expiring",
         "You have {points} points expiring soon. "
         "Redeem them before {date}!\n\nShop now at {store}.com"),
        ("New arrivals at {store}",
         "Check out the latest styles just in at {store}. "
         "Free shipping on orders over ${amount}."),
        ("You're invited: {event}",
         "Join us for {event} at {location}.\n\n"
         "RSVP by {date}.\n\nHope to see you there!"),
        ("Weekly ad: {store}",
         "This week's deals at {store}:\n\n"
         "- {item1}: ${price1}\n- {item2}: ${price2}\n- {item3}: ${price3}\n\n"
         "Valid through {date}."),
    ],
    "scam": [
        ("URGENT: Your account has been suspended",
         "Dear Valued Customer,\n\nWe detected unusual activity on your account. "
         "Your account has been temporarily suspended.\n\n"
         "Verify your identity immediately to restore access: {link}\n\n"
         "Failure to verify within 24 hours will result in permanent closure."),
        ("You've won ${amount}!",
         "CONGRATULATIONS!\n\nYou have been selected as the winner of ${amount} "
         "in our international lottery!\n\nTo claim your prize, send your full name, "
         "address, and bank details to claim your winnings.\n\nAct fast!"),
        ("IRS: Final notice",
         "This is your final notice from the Internal Revenue Service.\n\n"
         "You owe ${amount} in back taxes. If you do not pay immediately, "
         "a warrant will be issued for your arrest.\n\n"
         "Pay now via gift card or wire transfer to avoid legal action."),
        ("Your package could not be delivered",
         "USPS: Your package is being held at our facility due to insufficient address.\n\n"
         "Update your address and pay the ${fee} redelivery fee here: {link}\n\n"
         "Package will be returned to sender in 48 hours."),
        ("Medicare: Your benefits are expiring",
         "Dear Beneficiary,\n\nYour Medicare benefits will be terminated unless "
         "you verify your information immediately.\n\n"
         "Call now to speak with a representative. Have your Medicare number ready."),
        ("Grandma, I need help",
         "Hi Grandma,\n\nI'm in trouble and I need your help. I was arrested "
         "and I need ${amount} for bail. Please don't tell Mom and Dad.\n\n"
         "Send the money via {payment} to this account. I'll explain later.\n\n"
         "I love you."),
    ],
}

# Slot values
AMOUNTS = ["47.82", "89.99", "124.50", "250.00", "1,500.00", "5,000.00"]
DATES = ["October 15", "November 1", "October 28", "next Friday", "the 15th"]
TIMES = ["9:00 AM", "2:30 PM", "11:15 AM", "4:00 PM"]
CLINICS = ["Main Street Clinic", "Riverside Medical", "Community Health Center"]
MEDS = ["Lisinopril", "Metformin", "Atorvastatin", "Levothyroxine"]
TOPICS = ["Weekend plans", "Thanksgiving", "Your birthday", "The kids", "Garden update"]
MESSAGES = [
    "How are you feeling? I hope your knee is better.",
    "The kids made you a card. I'll bring it by this weekend.",
    "Did you watch the game last night? What a finish!",
    "Can you send me your recipe for apple pie?",
    "We're thinking of visiting next month. Does that work?",
]
EVENTS = ["the wedding", "graduation", "the reunion", "last weekend"]
PERCENTS = ["20", "30", "40", "50"]
POINTS = ["500", "1,200", "2,500"]
ITEMS = ["Chicken breast", "Ground beef", "Coffee", "Paper towels", "Milk"]
PRICES = ["3.99", "5.49", "8.99", "2.50"]
LINKS = ["http://secure-verify.net", "http://account-restore.com", "http://usps-hold.info"]
PAYMENTS = ["gift cards", "Bitcoin", "wire transfer", "Zelle"]
FEES = ["1.99", "2.99", "4.99"]


def fill(template: str, rng: random.Random) -> str:
    text = template
    slots = {
        "company": rng.choice(COMPANIES),
        "name": rng.choice(NAMES),
        "pharmacy": rng.choice(PHARMACIES),
        "store": rng.choice(STORES),
        "amount": rng.choice(AMOUNTS),
        "date": rng.choice(DATES),
        "time": rng.choice(TIMES),
        "clinic": rng.choice(CLINICS),
        "med": rng.choice(MEDS),
        "topic": rng.choice(TOPICS),
        "message": rng.choice(MESSAGES),
        "event": rng.choice(EVENTS),
        "percent": rng.choice(PERCENTS),
        "points": rng.choice(POINTS),
        "item1": rng.choice(ITEMS),
        "item2": rng.choice(ITEMS),
        "item3": rng.choice(ITEMS),
        "price1": rng.choice(PRICES),
        "price2": rng.choice(PRICES),
        "price3": rng.choice(PRICES),
        "link": rng.choice(LINKS),
        "payment": rng.choice(PAYMENTS),
        "fee": rng.choice(FEES),
        "location": rng.choice(CLINICS),
    }
    for key, value in slots.items():
        text = text.replace("{" + key + "}", value, 1)
    return text


def generate(category: str, templates: list, n: int, rng: random.Random) -> list:
    records = []
    for _ in range(n):
        subject, body = rng.choice(templates)
        subject_filled = fill(subject, rng)
        body_filled = fill(body, rng)
        text = f"Subject: {subject_filled}\n\n{body_filled}"
        records.append({
            "text": text,
            "label": category,
            "category": category,
            "source": "synthetic",
        })
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="mail_corpus.jsonl")
    ap.add_argument("--n-per-category", type=int, default=300)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    records = []
    for category, templates in EMAILS.items():
        records.extend(generate(category, templates, args.n_per_category, rng))

    rng.shuffle(records)

    with open(args.out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} records to {args.out}")
    for category in sorted(EMAILS.keys()):
        count = sum(1 for r in records if r["label"] == category)
        print(f"  {category}: {count}")


if __name__ == "__main__":
    main()
