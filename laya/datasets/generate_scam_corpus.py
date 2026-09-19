#!/usr/bin/env python3
"""
Generate the scam-screen training corpus for the Laya fine-tune.

Two sources:
  1. Synthetic elder-fraud messages, built from FTC elder-fraud categories
     (seed templates with combinatorial variation).
  2. Legitimate messages an elderly person actually receives (bills, medical
     reminders, family texts, package notifications) — the hard negatives.

Output: JSONL, one record per line:
  {"text": "...", "label": "scam"|"legit", "category": "...", "source": "synthetic"}

Labels map to the scam-screen question pack (laya/questions/scam-screen.json):
  scam  -> is_scam noul target ~1.0
  legit -> is_scam noul target ~0.0

usage: python generate_scam_corpus.py --out scam_corpus.jsonl [--n-scam 800] [--n-legit 800] [--seed 42]
"""
import argparse
import json
import random

# ---------------------------------------------------------------------------
# Scam templates. Each is (category, template, slots). Slots are lists of
# interchangeable phrases; the generator samples one per slot.
# Categories follow FTC elder-fraud reporting categories.
# ---------------------------------------------------------------------------

URGENCY = ["immediately", "within 24 hours", "today", "right away", "before end of business"]
PAYMENT = ["gift cards", "wire transfer", "Bitcoin", "Zelle", "a prepaid card"]
AGENCY = ["the IRS", "Social Security Administration", "Medicare", "your bank's fraud department", "the FBI"]
THREAT = ["your account will be suspended", "a warrant will be issued for your arrest",
          "your benefits will be terminated", "legal action will be taken against you",
          "your Social Security number will be blocked"]

SCAM_TEMPLATES = [
    # Government impersonation
    ("gov_impersonation",
     "This is {agency}. Our records show suspicious activity linked to your Social Security number. "
     "You must call us back {urgency} or {threat}.", {}),
    ("gov_impersonation",
     "URGENT: {agency} has detected unauthorized use of your SSN in Texas. "
     "To avoid {threat}, press 1 to speak with an officer {urgency}.", {}),
    # Medicare / health
    ("medicare",
     "Dear beneficiary, your Medicare card is expiring. To receive your new card with updated benefits, "
     "confirm your Medicare number and date of birth by replying to this message {urgency}.", {}),
    ("medicare",
     "You qualify for a FREE back brace covered 100% by Medicare. Just verify your Medicare ID "
     "and shipping address. Supplies are limited — act {urgency}.", {}),
    # Utility shutoff
    ("utility_shutoff",
     "ALERT from your utility provider: Your service is scheduled for disconnection {urgency} "
     "due to an unpaid balance. Pay now via {payment} to avoid shutoff. Call the number below.", {}),
    # Grandparent scam
    ("grandparent",
     "Grandma, it's me. I'm in trouble and I need your help. I was in an accident and I'm at the police station. "
     "Please don't tell mom and dad. I need ${amount} for bail. You can send it by {payment}. "
     "I'll explain everything later, please hurry.", {"amount": ["500", "1,200", "2,000", "800"]}),
    ("grandparent",
     "Hi Grandma, this is your grandson. My phone broke so I'm texting from a friend's number. "
     "I need ${amount} for a car repair, can you Zelle me? I'll pay you back Friday. "
     "Don't call my old number, it's disconnected.", {"amount": ["300", "450", "600"]}),
    # Package delivery
    ("package",
     "USPS: Your package could not be delivered due to an incomplete address. "
     "Update your address within 12 hours to avoid return to sender: {link}", {}),
    ("package",
     "FedEx: A package addressed to you is being held at our facility. "
     "A ${fee} redelivery fee is required. Pay here: {link}", {"fee": ["1.99", "2.99", "0.99"]}),
    # Bank fraud
    ("bank_fraud",
     "ALERT: A charge of ${amount} was attempted on your debit card at {merchant}. "
     "If this wasn't you, verify your identity {urgency} by clicking: {link}",
     {"amount": ["847.22", "1,299.00", "499.99"], "merchant": ["Walmart.com", "Amazon", "an online retailer"]}),
    ("bank_fraud",
     "Your online banking has been locked after 3 failed login attempts. "
     "Restore access by confirming your username, password, and the last 4 of your SSN: {link}", {}),
    # Tech support
    ("tech_support",
     "WARNING: Your Windows computer has been infected with a virus. "
     "Call Microsoft Support at the number below {urgency}. Do not restart your computer.", {}),
    ("tech_support",
     "Your iCloud account has been compromised. Apple Support needs to verify your identity. "
     "Have your Apple ID password and payment method ready when you call.", {}),
    ("tech_support",
     "This is Geek Squad. We detected a problem with your {device} during a routine scan. "
     "To fix it remotely, we need you to install a small tool. Go to {link} and enter the code we give you.",
     {"device": ["laptop", "computer", "iPad", "router"]}),
    ("tech_support",
     "Your antivirus subscription has expired. Your device is UNPROTECTED. "
     "Renew now for ${amount}/year or your files may be at risk. Call to renew: 1-800-555-0199.",
     {"amount": ["49.99", "79.99", "99.99"]}),
    ("tech_support",
     "ALERT: Suspicious sign-in to your email from Russia. If this wasn't you, "
     "secure your account now by calling support. Have your password ready to verify.", {}),
    ("tech_support",
     "Comcast/Xfinity: We've detected unusual activity on your home network. "
     "A technician needs to run a remote diagnostic. Please allow remote access when prompted.", {}),
    # Sweepstakes / prize
    ("sweepstakes",
     "CONGRATULATIONS! You've won the Publishers Clearing House grand prize of $2.5 million! "
     "To claim your winnings, pay the ${fee} processing fee via {payment}.",
     {"fee": ["250", "500", "1,000"]}),
    # Romance / companionship
    ("romance",
     "Good morning beautiful. I've been thinking about you all night. I wish I could visit but my "
     "oil rig contract keeps me overseas. My wallet was stolen — can you help with ${amount} "
     "until my next paycheck? I love you.", {"amount": ["200", "500", "1,500"]}),
]

# Fill-in values for slots referenced in templates
LINKS = ["http://usps-redelivery.info", "http://fedex-hold.center", "http://secure-verify-login.com",
         "http://account-restore.net", "http://medicare-renewal.org"]

# ---------------------------------------------------------------------------
# Legitimate templates — the hard negatives. These MUST look similar to scams
# (bills, delivery notices, bank alerts) so the model learns the difference.
# ---------------------------------------------------------------------------

LEGIT_TEMPLATES = [
    ("utility_bill",
     "Your Consumers Energy bill for ${amount} is ready. Payment is due on {date}. "
     "View your bill and pay at consumersenergy.com.",
     {"amount": ["87.43", "112.18", "94.60"], "date": ["October 3", "October 15", "November 1"]}),
    ("medical_reminder",
     "Reminder: You have an appointment with Dr. {name} on {date} at {time}. "
     "Reply CONFIRM or call the office to reschedule.",
     {"name": ["Patel", "Nguyen", "Kowalski"], "date": ["Tuesday, Oct 7", "Friday, Oct 10"],
      "time": ["9:30 AM", "2:15 PM", "11:00 AM"]}),
    ("family_text",
     "Hi Mom, it's {name}. Can you pick up {item} when you're at the store? "
     "Love you, talk soon.",
     {"name": ["Sarah", "Mike", "Jen"], "item": ["milk and eggs", "your prescription", "bread"]}),
    ("package_legit",
     "Your Amazon package was delivered. It was left at the front door. "
     "Track your packages at amazon.com.", {}),
    ("bank_legit",
     "Your statement is ready. Log in to your account at chase.com to view it. "
     "If you have questions, call the number on the back of your card.", {}),
    ("church_community",
     "Reminder: The {org} potluck is this Sunday after service. "
     "Please bring a dish to share. Contact {name} with questions.",
     {"org": ["First Baptist", "St. Mary's", "Community Center"], "name": ["Linda", "Pastor Dave", "Ruth"]}),
    ("pharmacy",
     "Your prescription at {pharmacy} is ready for pickup. "
     "Pickup by {date}. Questions? Call the pharmacy.",
     {"pharmacy": ["CVS", "Walgreens", "Kroger Pharmacy"], "date": ["Friday", "Oct 10", "this week"]}),
    # --- Hard negatives: legit messages that share surface features with scams ---
    ("bank_legit",
     "FRAUD ALERT from {bank}: Did you attempt a purchase of ${amount} at {merchant}? "
     "Reply YES or NO. If NO, we'll block the card and send a replacement. "
     "Or call the number on the back of your card.",
     {"bank": ["Chase", "Bank of America", "your credit union"],
      "amount": ["62.18", "143.50", "28.99"], "merchant": ["Meijer", "Shell", "Walgreens"]}),
    ("bank_legit",
     "Unusual sign-in activity on your {bank} account from a new device. "
     "If this was you, no action is needed. If not, visit {bank}.com or call us directly.",
     {"bank": ["Chase", "Wells Fargo", "Citibank"]}),
    ("tech_support_legit",
     "Your {service} subscription renews on {date} for ${amount}. "
     "Manage your subscription in your account settings. No action needed to continue.",
     {"service": ["Norton AntiVirus", "Microsoft 365", "McAfee"],
      "date": ["Oct 12", "Nov 1", "Oct 28"], "amount": ["39.99", "69.99", "99.99"]}),
    ("tech_support_legit",
     "A new device signed in to your Apple ID ({device}). "
     "If this was you, you can ignore this message. If not, change your password at appleid.apple.com.",
     {"device": ["iPhone 16", "iPad", "MacBook Air"]}),
    ("gov_legit",
     "This is a reminder from the Social Security Administration: your annual statement "
     "is available online at ssa.gov. We will never call to ask for your SSN or payment.", {}),
    ("medicare_legit",
     "Medicare Open Enrollment runs Oct 15 – Dec 7. Review your plan options at medicare.gov. "
     "Medicare will never call you to sell a plan or ask for payment over the phone.", {}),
    ("utility_urgent_legit",
     "Consumers Energy: A payment of ${amount} is due in 3 days. "
     "Pay at consumersenergy.com or by phone at the number on your bill. "
     "If you've already paid, please disregard.",
     {"amount": ["87.43", "112.18", "94.60"]}),
    ("delivery_urgent_legit",
     "UPS: We attempted delivery but no one was home. Your package will be held at the "
     "{city} facility for 5 business days. Track at ups.com with your tracking number.",
     {"city": ["Grand Rapids", "Lansing", "Detroit"]}),
]


def fill(template: str, slots: dict, rng: random.Random) -> str:
    text = template
    # Built-in slots
    builtins = {
        "urgency": rng.choice(URGENCY),
        "payment": rng.choice(PAYMENT),
        "agency": rng.choice(AGENCY),
        "threat": rng.choice(THREAT),
        "link": rng.choice(LINKS),
    }
    builtins.update({k: rng.choice(v) for k, v in slots.items()})
    for key, value in builtins.items():
        text = text.replace("{" + key + "}", value)
    return text


def generate(templates, label, n, rng):
    records = []
    for _ in range(n):
        category, template, slots = rng.choice(templates)
        records.append({
            "text": fill(template, slots, rng),
            "label": label,
            "category": category,
            "source": "synthetic",
        })
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="scam_corpus.jsonl")
    ap.add_argument("--n-scam", type=int, default=800)
    ap.add_argument("--n-legit", type=int, default=800)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    records = generate(SCAM_TEMPLATES, "scam", args.n_scam, rng)
    records += generate(LEGIT_TEMPLATES, "legit", args.n_legit, rng)
    rng.shuffle(records)

    with open(args.out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    scam = sum(1 for r in records if r["label"] == "scam")
    legit = len(records) - scam
    print(f"Wrote {len(records)} records to {args.out} ({scam} scam, {legit} legit)")
    cats = {}
    for r in records:
        cats[r["category"]] = cats.get(r["category"], 0) + 1
    for cat, count in sorted(cats.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
