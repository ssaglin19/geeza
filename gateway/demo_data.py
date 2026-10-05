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
