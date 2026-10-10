"""Synthetic demo data: fake emails, a fake vendor, fake amounts. Nothing here is real."""

EMAILS = [
    {"id": "1", "from": "Ruth (daughter) <ruth.miller@example.com>", "subject": "Sunday dinner?",
     "body": "Hi Mom, are you still free Sunday at 5? I will bring the pie. Love, Ruth"},
    {"id": "2", "from": "Lakeshore Power <billing@lakeshore-power.test>", "subject": "Your January bill is ready",
     "body": "Your statement is ready. Amount due: $86.90, due Jan 28. You can pay from your account page.",
     "claims_to_be_domain": "lakeshore-power.test"},
    {"id": "3", "from": "Medicare Support <help@medicare-benefits-update.test>", "subject": "FINAL NOTICE: coverage suspended",
     "body": "Your Medicare coverage will be suspended within 24 hours. Reply now with your Social Security number and buy two gift cards to confirm your identity.",
     "claims_to_be_domain": "medicare.gov"},
    {"id": "4", "from": "Dr. Patel's office <frontdesk@patelfamilymed.test>", "subject": "Appointment reminder",
     "body": "A reminder that you have a checkup Thursday at 10:15 AM. Please bring your medication list."},
]

LAST_BILL = 84.00
# Vendor's displayed amount per scenario. The amount-sanity gate compares it to LAST_BILL.
SCENARIOS = {"normal": "86.90", "suspicious": "412.00"}


# Known sources: senders the caregiver (Sean) installed as trusted for the demo persona. Invented data,
# same status as the memory seed. A payment request from one of these does not trigger the scam warning.
KNOWN_SOURCES = ["lakeshore-power.test", "patelfamilymed.test", "ruth.miller@example.com"]


# Electric bill history for the bill explainer (synthetic). Rate is dollars per kWh.
BILL_HISTORY = [
    {"period": "Aug", "days": 31, "kwh": 560, "rate": 0.138, "fixed": 12.38, "extras": []},
    {"period": "Sep", "days": 30, "kwh": 505, "rate": 0.138, "fixed": 12.38, "extras": []},
    {"period": "Oct", "days": 31, "kwh": 470, "rate": 0.138, "fixed": 12.38, "extras": []},
    {"period": "Nov", "days": 30, "kwh": 498, "rate": 0.138, "fixed": 12.38, "extras": []},
    {"period": "Dec", "days": 31, "kwh": 519, "rate": 0.138, "fixed": 12.38, "extras": []},
]
# January statement per scenario. "suspicious" matches the $412.00 amount in SCENARIOS.
BILL_CURRENT = {
    "normal": {"period": "January", "days": 31, "kwh": 540, "rate": 0.138, "fixed": 12.38, "extras": []},
    "suspicious": {"period": "January", "days": 31, "kwh": 1240, "rate": 0.138, "fixed": 12.38,
                   "extras": [{"label": "Prior-period estimate adjustment", "amount": 228.50}]},
}
