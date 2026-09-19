#!/usr/bin/env python3
"""
Generate the mail-triage training corpus for the Laya fine-tune.

Five categories: bill, medical, personal, junk, scam.
Each email has Subject + body format. Scam emails mirror the scam-screen
corpus patterns (urgency, threats, payment demands).

Output: JSONL, one record per line:
  {"text": "Subject: ...\n\n...", "label": "bill"|"medical"|"personal"|"junk"|"scam", "category": "...", "source": "synthetic"}

usage: python generate_mail_corpus.py --out mail_corpus.jsonl [--n-per-category 200] [--seed 42]
"""
import argparse
import json
import random

# ---------------------------------------------------------------------------
# Bill emails — legitimate utility, credit card, insurance bills
# ---------------------------------------------------------------------------

BILL_TEMPLATES = [
    ("utility",
     "Subject: Your {company} bill is ready\n\n"
     "Dear Customer,\n\n"
     "Your {company} bill for ${amount} is now available. Payment is due on {date}.\n\n"
     "View your bill and pay online at {website}.\n\n"
     "Thank you,\n{company} Customer Service",
     {"company": ["Consumers Energy", "DTE Energy", "Comcast", "AT&T"],
      "amount": ["87.43", "112.18", "94.60", "156.22"],
      "date": ["October 3", "October 15", "November 1"],
      "website": ["consumersenergy.com", "dteenergy.com", "xfinity.com", "att.com"]}),
    ("credit_card",
     "Subject: Your {bank} statement is ready\n\n"
     "Your {bank} credit card statement for the period ending {date} is available.\n\n"
     "Minimum payment: ${min_payment}\n"
     "Due date: {due_date}\n\n"
     "Log in to your account at {bank}.com to view details.",
     {"bank": ["Chase", "Bank of America", "Capital One", "Discover"],
      "date": ["September 15", "September 30"],
      "min_payment": ["25.00", "35.00", "50.00"],
      "due_date": ["October 10", "October 22"]}),
    ("insurance",
     "Subject: {company} Premium Notice\n\n"
     "Dear Policyholder,\n\n"
     "Your {company} insurance premium of ${amount} is due on {date}.\n\n"
     "Policy number: {policy}\n"
     "Coverage period: {period}\n\n"
     "Pay online at {company}.com or call us at the number on your policy.",
     {"company": ["State Farm", "Geico", "Progressive", "Allstate"],
      "amount": ["234.50", "189.99", "312.75"],
      "date": ["October 1", "October 15"],
      "policy": ["POL-123456", "POL-789012"],
      "period": ["Oct 2024 - Mar 2025", "Nov 2024 - Apr 2025"]}),
]

# ---------------------------------------------------------------------------
# Medical emails — appointments, test results, prescription reminders
# ---------------------------------------------------------------------------

MEDICAL_TEMPLATES = [
    ("appointment",
     "Subject: Appointment Reminder: Dr. {doctor}\n\n"
     "Dear {name},\n\n"
     "This is a reminder of your appointment with Dr. {doctor} on {date} at {time}.\n\n"
     "Location: {location}\n"
     "Please arrive 15 minutes early to complete paperwork.\n\n"
     "To reschedule, call our office at {phone}.",
     {"doctor": ["Patel", "Nguyen", "Kowalski", "Smith"],
      "name": ["Mary", "John", "Robert", "Patricia"],
      "date": ["Tuesday, October 7", "Friday, October 10", "Monday, October 13"],
      "time": ["9:30 AM", "2:15 PM", "11:00 AM"],
      "location": ["Main Street Medical Center", "Downtown Clinic", "Community Health"],
      "phone": ["(555) 123-4567", "(555) 987-6543"]}),
    ("test_results",
     "Subject: Your test results are available\n\n"
     "Dear {name},\n\n"
     "Your recent lab results are now available in your patient portal.\n\n"
     "Log in at {portal} to view your results.\n\n"
     "If you have questions, contact your doctor's office.",
     {"name": ["Mary", "John", "Robert"],
      "portal": ["mychart.healthsystem.org", "patientportal.clinic.com"]}),
    ("prescription",
     "Subject: Prescription Ready for Pickup\n\n"
     "Your prescription at {pharmacy} is ready for pickup.\n\n"
     "Medication: {medication}\n"
     "Pickup by: {date}\n\n"
     "Questions? Call the pharmacy at {phone}.",
     {"pharmacy": ["CVS", "Walgreens", "Rite Aid", "Kroger Pharmacy"],
      "medication": ["Lisinopril 10mg", "Metformin 500mg", "Atorvastatin 20mg"],
      "date": ["Friday, October 10", "this week"],
      "phone": ["(555) 123-4567"]}),
]

# ---------------------------------------------------------------------------
# Personal emails — family, friends, community
# ---------------------------------------------------------------------------

PERSONAL_TEMPLATES = [
    ("family",
     "Subject: Re: {subject}\n\n"
     "Hi {name},\n\n"
     "{message}\n\n"
     "Love,\n{sender}",
     {"subject": ["Weekend plans", "Garden update", "Birthday party", "Thanksgiving"],
      "name": ["Mom", "Dad", "Grandma", "Grandpa"],
      "message": [
          "The kids made you a card. I'll bring it by this weekend.",
          "Can you pick up milk and eggs when you're at the store?",
          "Don't forget Sarah's birthday is next Saturday. Party at 2pm.",
          "Are you still hosting Thanksgiving this year? Let me know what to bring."
      ],
      "sender": ["Sarah", "Mike", "Jen", "David"]}),
    ("friend",
     "Subject: {subject}\n\n"
     "Hi {name},\n\n"
     "{message}\n\n"
     "Best,\n{sender}",
     {"subject": ["Book club", "Lunch next week", "Church potluck"],
      "name": ["Mary", "John"],
      "message": [
          "Book club is moved to Thursday this month. Same time, same place.",
          "Want to meet for lunch next Tuesday? The usual spot?",
          "The church potluck is this Sunday after service. Bring a dish to share."
      ],
      "sender": ["Linda", "Ruth", "Pastor Dave"]}),
]

# ---------------------------------------------------------------------------
# Junk emails — newsletters, promotions, spam (not malicious, just unwanted)
# ---------------------------------------------------------------------------

JUNK_TEMPLATES = [
    ("newsletter",
     "Subject: {company} Weekly Deals\n\n"
     "This week's specials at {company}:\n\n"
     "- {item1}: {price1}\n"
     "- {item2}: {price2}\n"
     "- {item3}: {price3}\n\n"
     "Shop now at {company}.com",
     {"company": ["Kroger", "Meijer", "Walmart", "Target"],
      "item1": ["Ground beef", "Milk", "Bread"],
      "price1": ["$4.99/lb", "$2.49", "$1.99"],
      "item2": ["Chicken breast", "Eggs", "Cereal"],
      "price2": ["$5.99/lb", "$3.29", "$3.49"],
      "item3": ["Apples", "Coffee", "Pasta"],
      "price3": ["$1.99/lb", "$8.99", "$1.49"]}),
    ("promotion",
     "Subject: {offer} at {company}\n\n"
     "Limited time offer!\n\n"
     "{description}\n\n"
     "Use code {code} at checkout.\n\n"
     "Shop now: {company}.com",
     {"offer": ["20% off", "Buy one get one free", "Free shipping"],
      "company": ["Macy's", "Kohl's", "JCPenney"],
      "description": [
          "Save on fall clothing for the whole family.",
          "Stock up on home essentials.",
          "New arrivals are here."
      ],
      "code": ["SAVE20", "BOGO", "FREESHIP"]}),
]

# ---------------------------------------------------------------------------
# Scam emails — phishing, fraud, malicious
# ---------------------------------------------------------------------------

SCAM_TEMPLATES = [
    ("gov_impersonation",
     "Subject: {agency}: {subject}\n\n"
     "Dear {name},\n\n"
     "Our records show {problem}. You must {action} {urgency} or {threat}.\n\n"
     "Click here to verify: {link}\n\n"
     "Sincerely,\n{agency}",
     {"agency": ["IRS", "Social Security Administration", "Medicare"],
      "subject": ["Urgent: Account Suspension", "Final Notice", "Action Required"],
      "name": ["Taxpayer", "Beneficiary", "Citizen"],
      "problem": [
          "suspicious activity linked to your Social Security number",
          "unpaid taxes from 2023",
          "your Medicare card is expiring"
      ],
      "action": ["verify your identity", "update your information", "confirm your account"],
      "urgency": ["immediately", "within 24 hours", "today"],
      "threat": [
          "your account will be suspended",
          "a warrant will be issued for your arrest",
          "your benefits will be terminated"
      ],
      "link": ["http://irs-verify.net", "http://ssa-secure.org", "http://medicare-renewal.com"]}),
    ("bank_fraud",
     "Subject: ALERT: Suspicious Activity on Your Account\n\n"
     "Dear {name},\n\n"
     "We detected a charge of ${amount} at {merchant}. If this wasn't you, "
     "verify your identity {urgency} by clicking: {link}\n\n"
     "Your account may be limited until we hear from you.\n\n"
     "{bank} Fraud Department",
     {"name": ["Valued Customer", "Account Holder"],
      "amount": ["847.22", "1,299.00", "499.99"],
      "merchant": ["Walmart.com", "Amazon", "an online retailer"],
      "urgency": ["immediately", "within 24 hours"],
      "link": ["http://secure-verify-login.com", "http://account-restore.net"],
      "bank": ["Chase", "Bank of America", "Wells Fargo"]}),
    ("package",
     "Subject: {carrier}: Delivery Failed\n\n"
     "Your package could not be delivered due to an incomplete address.\n\n"
     "Update your address within 12 hours to avoid return to sender: {link}\n\n"
     "Tracking: {tracking}",
     {"carrier": ["USPS", "FedEx", "UPS"],
      "link": ["http://usps-redelivery.info", "http://fedex-hold.center"],
      "tracking": ["1Z999AA10123456784", "9400100000000000000000"]}),
]


def fill(template: str, slots: dict, rng: random.Random) -> str:
    text = template
    for key, values in slots.items():
        text = text.replace("{" + key + "}", rng.choice(values))
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
    ap.add_argument("--out", default="mail_corpus.jsonl")
    ap.add_argument("--n-per-category", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    records = []
    records += generate(BILL_TEMPLATES, "bill", args.n_per_category, rng)
    records += generate(MEDICAL_TEMPLATES, "medical", args.n_per_category, rng)
    records += generate(PERSONAL_TEMPLATES, "personal", args.n_per_category, rng)
    records += generate(JUNK_TEMPLATES, "junk", args.n_per_category, rng)
    records += generate(SCAM_TEMPLATES, "scam", args.n_per_category, rng)
    rng.shuffle(records)

    with open(args.out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    cats = {}
    for r in records:
        cats[r["label"]] = cats.get(r["label"], 0) + 1
    print(f"Wrote {len(records)} records to {args.out}")
    for cat, count in sorted(cats.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()