# Scam-screen eval (live demo, synthetic messages)

Run 2026-10-09 against the deployed demo at https://geeza.onrender.com (Nemotron Nano 30B A3B on Nebius Token Factory, rule layer plus model decision layer). This replaces the unmeasured numbers in the old handoff.

## Method

- 40 synthetic messages written for this eval: 20 scams (gift cards, fake agencies, grandparent scams, fake billing, phishing links, Medicare and bank lures) and 20 legitimate messages (family, real bills, pharmacy, doctor, utilities, two real-looking Social Security and bank notices).
- Each message was sent to `POST /message` as "Please check this message for scams: <text>", one sender id per message. When the demo asked "Did you want to check if something is a scam?", the eval replied YES, as a person would. The score is the final scam_check result.
- One run, no retries, no tuning against these messages. Messages are not drawn from real people or real accounts.

## Results

| | flagged scam | not flagged |
|---|---|---|
| scam (20) | 20 | 0 |
| legitimate (20) | 2 | 18 |

- Scam recall: 20/20. Legitimate pass-through: 18/20. Precision: 20/22 (91%). Accuracy: 38/40 (95%).
- Both false positives were real-looking notices that mention a Social Security payment or a bank statement (rows 33 and 34). The screen treated "credentials or ID numbers" wording as a scam sign even though both messages say to use the official site. For a protective assistant, a false alarm sends the person to ask a caregiver; a miss costs money. We do not claim this tradeoff is tuned.
- 8 of 40 messages needed the YES step because intent routing was only medium confidence. Not an accuracy issue, but it adds a step.

## What this does and does not show

- n=40, hand-written by us. Small, and the scams are fairly classic. It says nothing about novel or targeted scams.
- Probabilities are the model's own and are not calibrated. This is not the Laya or Bonsai pipeline from the original spec.
- Rerun by sending the messages below to the demo. The demo limits each IP to 60 messages per hour.

## Messages

| # | label | flagged | text |
|---|---|---|---|
| 1 | scam | yes | USPS: Your package is held. Pay a $1.99 redelivery fee at usps-track-help.top/pay today or it will be returned. |
| 2 | scam | yes | FINAL NOTICE: Your Medicare coverage is suspended. Call 1-888-555-0142 now and have your Medicare number ready. |
| 3 | scam | yes | Grandma it's me, I'm in jail and need bail money. Please don't tell Mom. Send gift cards, I'll explain later. |
| 4 | scam | yes | Your Social Security number has been linked to illegal activity. Press 1 to speak to an agent or a warrant will be issued. |
| 5 | scam | yes | Amazon: a $899.99 charge was made on your account. If this was not you, call 1-855-555-0188 to cancel immediately. |
| 6 | scam | yes | Congratulations! You won a $500 Walmart gift card. Claim now at walmart-rewards-win.click, only 2 left. |
| 7 | scam | yes | Bank of America alert: your account is locked. Verify your login at bofa-secure-verify.info within 24 hours. |
| 8 | scam | yes | Your computer has a virus. Microsoft support detected it. Call us at 1-866-555-0123 and allow remote access to fix it. |
| 9 | scam | yes | IRS: you owe $4,312 in back taxes. Pay today with Apple gift cards to avoid arrest. |
| 10 | scam | yes | Hello dear, I am a lonely soldier overseas. I need you to help me move $2 million. You will keep 20 percent. |
| 11 | scam | yes | Your Netflix payment failed. Update your card at netflix-billing-update.co now or your account will be closed. |
| 12 | scam | yes | Hi, this is your grandson. I had a car accident and need $2,000 by Western Union right now. Don't call anyone. |
| 13 | scam | yes | Verify your Medicare card is still active. Reply with your card number and date of birth to keep your benefits. |
| 14 | scam | yes | Your electric bill is 2 months overdue. Pay $340 now by Zelle to 555-0199 or power will be cut in one hour. |
| 15 | scam | yes | Pharmacy notice: your prescription is ready, but we need your credit card number and PIN to release it. Reply now. |
| 16 | scam | yes | Dear customer, your Chase debit card was used in Texas. Reply with the 6 digit code we just texted you to block it. |
| 17 | scam | yes | Social Security Administration: a cost of living increase is pending. Confirm your bank login at ssa-benefit-update.top. |
| 18 | scam | yes | Geek Squad renewal: $349.99 will be charged today. To cancel call 1-877-555-0166 immediately. |
| 19 | scam | yes | You have been selected for a free senior medical alert device. Just confirm your bank account number to ship it. |
| 20 | scam | yes | Your Venmo account has a pending payment of $750. Click venmo-claim-funds.xyz to accept before it expires. |
| 21 | legit | no | Hi Mom, it's Ruth. Are you free Sunday at five for dinner? I'll bring the pie. |
| 22 | legit | no | Lakeshore Power: your January bill is $86.90, due Jan 28. You can pay on our website or by mail. Thank you. |
| 23 | legit | no | Reminder from Dr. Patel's office: your appointment is Tuesday at 10:30 AM. Call the office if you need to reschedule. |
| 24 | legit | no | Your Walgreens prescription is ready for pickup at the store on Main Street. Pickup hours are 9 to 9. |
| 25 | legit | no | Hello from your grandson Tyler. Got the birthday card, thank you! Love you, talk Sunday. |
| 26 | legit | no | Your library hold on the book "The Thursday Murder Club" is ready. It will be held for 7 days. |
| 27 | legit | no | Consumers Energy: your scheduled payment of $72.40 posted on Jan 15. Thank you for your payment. |
| 28 | legit | no | Church bulletin: potluck is this Saturday at noon in the fellowship hall. Bring a dish to share. |
| 29 | legit | no | Hi Dad, the plumber is coming Thursday between 1 and 3. I'll be there so you don't need to be home. |
| 30 | legit | no | Your car is due for an oil change. Schedule at Jones Auto, 414-555-0111, or reply STOP to opt out. |
| 31 | legit | no | Medicare Summary Notice: your latest statement is available at medicare.gov when you log in. No action needed. |
| 32 | legit | no | Neighbor Joan: I put your newspaper inside the door. Hope the knee is feeling better! |
| 33 | legit | yes | Your Social Security payment of $1,812 will be deposited on the 3rd. Visit ssa.gov to view your statement. |
| 34 | legit | yes | Chase: your statement is ready. Sign in at chase.com to view it. We will never ask for your password by text. |
| 35 | legit | no | Pharmacy: you have 1 refill left on your lisinopril. Call 414-555-0170 or use the app to request it. |
| 36 | legit | no | Hi Grandpa, my flight lands at 4:15 Friday. Can you pick me up or should I take an Uber? Mom knows. |
| 37 | legit | no | Water utility notice: street work on Elm Ave Monday 8 to 4. Water may be briefly off. No action required. |
| 38 | legit | no | Your doctor's office sent a new message in the patient portal. Log in at your usual portal to read it. |
| 39 | legit | no | Amazon: your order of a pill organizer has shipped and arrives Thursday. Track it in your Amazon app. |
| 40 | legit | no | Insurance: your annual premium of $412 is due Feb 1. You can pay by check or online, no rush before the date. |
