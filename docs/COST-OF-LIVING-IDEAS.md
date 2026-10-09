# Cost-of-living ideas for Geeza

Idea source: a thread Sean saved, October 8, 2026. Paraphrased here; the original author is not identified.

## Direction

Personal assistants should lead with relief from everyday financial pressure, rather than treating travel, reservations and party planning as the main pitch. Lower household costs, less paperwork and fewer expensive mistakes are concrete reasons to use an assistant. Helping many households with those problems could also build public trust in AI.

For Geeza, this is an ideas backlog, not a change to the current build spec or hackathon demo. None of the workflows below is claimed to be implemented. Older adults and their caregivers are a natural audience for some of these tasks; the broader household examples are preserved without pretending every one is elderly-specific.

## 1. Prescription costs

**Need:** A person taking several medications wants to know whether refills could cost less.

**Possible workflow:** Compare the person's insurance copays with GoodRx, Cost Plus Drugs and nearby pharmacies for the same drug, strength, quantity and refill. Identify usable discounts, help arrange an approved pharmacy transfer, and check prices again before future refills.

**Success:** Verified out-of-pocket savings without a missed refill or an unapproved medication change.

**Geeza fit:** Strong fit for older adults managing recurring prescriptions and caregivers helping with refills. A pharmacist or prescriber must handle clinical questions; cheaper does not mean medically interchangeable.

## 2. Groceries without changing the household's meals

**Need:** Reduce a regular grocery bill while keeping the foods the household actually eats.

**Possible workflow:** Read receipt photos, compare local stores and coupons, suggest acceptable lower-cost equivalents, prepare a cart, and track actual weekly savings. Include delivery charges, travel and minimum-order rules in the comparison.

**Success:** A lower final grocery total while keeping dietary needs, preferred meals and practical shopping arrangements intact.

**Geeza fit:** Useful for people on fixed incomes and caregivers who already organize shopping. Substitutions remain the person's choice.

## 3. Credit card debt

**Need:** Understand the cost of balances spread across cards and find a repayment path the household can afford.

**Possible workflow:** Calculate interest and payment scenarios from current statements, investigate issuer hardship programs and balance-transfer offers, draft requests to issuers, and build a repayment schedule against the actual household budget.

**Success:** An understandable, affordable plan with total costs and tradeoffs shown, not merely a lower advertised interest rate.

**Guard:** Include transfer fees, promotional expiry, eligibility and credit effects. No new account or transfer without approval. This is preparation and comparison, not a promise of financial results.

## 4. Car insurance renewal

**Need:** A renewal increase prompts a search for a less expensive policy.

**Possible workflow:** Read the current policy, obtain competing quotes with matching coverage limits and deductibles, check discounts, and prepare a switch timed to avoid a coverage gap.

**Success:** A verified premium comparison and, if chosen, replacement coverage active before the old policy ends.

**Geeza fit:** Useful for older drivers and caregivers helping with renewals. Do not hide reduced coverage inside a cheaper quote or cancel before replacement coverage is confirmed.

## 5. Internet bills

**Need:** A household suspects its monthly internet bill is too high.

**Possible workflow:** Compare available service at the address, check eligibility for promotions, prepare or conduct an approved retention conversation, and present the best usable offer before changing service.

**Success:** Lower total cost for suitable service, with equipment charges, promotional expiry and cancellation costs included.

**Geeza fit:** Recurring bills are a good fit for older households. Keep essential connectivity working; a cheaper headline rate alone is not a win.

## 6. Car repair estimates

**Need:** A person cannot tell whether a large repair estimate is fair.

**Possible workflow:** Break the estimate into parts and labor, compare relevant labor times and parts prices, find nearby shops, request itemized competing quotes, and arrange an approved second opinion.

**Success:** A clear explanation of the estimate and comparable quotes or a qualified second opinion before committing to repairs.

**Guard:** Remote price research is not a diagnosis. Do not advise driving an unsafe car; get a mechanic's assessment when safety is uncertain.

## 7. Benefits and assistance

**Need:** A household struggling with bills wants to find help it may be missing.

**Possible workflow:** Screen current eligibility rules for SNAP, Medicaid/CHIP, utility assistance and tax credits; assemble documents; prepare applications for review; and track submission and renewal deadlines.

**Success:** Eligible support identified and approved applications submitted with receipts and follow-up dates tracked. Never promise acceptance from an initial screening.

**Geeza fit:** Benefits navigation can help older adults and caregivers. CHIP and child-related credits belong to the broader family-household case, not an elderly-only pitch. Eligibility must use the person's actual circumstances and local rules.

## 8. Rent increases

**Need:** A tenant faces a renewal increase they cannot afford.

**Possible workflow:** Check local rent rules and lease terms, compare relevant nearby listings, document maintenance issues, draft a supported counteroffer, and help with approved negotiation messages.

**Success:** A documented set of lawful options and, if negotiation works, confirmed renewal terms the tenant understands.

**Geeza fit:** Useful for older renters on fixed incomes. Do not claim a legal entitlement without checking the jurisdiction; involve a tenant organization or lawyer when needed.

## 9. Electric bill spikes

**Need:** A much higher bill needs an explanation, not just another payment reminder.

**Possible workflow:** Read bills and usage data, compare billing periods and rate plans, look for unusual consumption, find applicable rebates or assistance, and help request a billing review.

**Success:** Explain the increase with evidence, identify useful next steps, and track any correction or savings through the next bill.

**Geeza fit:** Directly related to the project's utility-bill theme, but investigating a bill and reducing its cost would be new work beyond the fake-vendor demo. Preserve safe heating, cooling and medical-equipment use.

## How to turn an idea into a bounded flow

Each candidate needs a defined input set, a repeatable process, and an observable finish: a comparable quote, a reviewed application, a confirmed correction, or actual savings after fees. Research and drafts should come before commitments.

- Start with one narrow workflow and fixture data; do not treat this list as a scheduled roadmap.
- Keep the existing code-owned approval gates. Show the exact price, recipient, terms or account change before any spending, sending, transfer, cancellation or submission.
- Stop on uncertain facts, broken flows or unsafe tradeoffs; make caregiver help available when the person has authorized it.
- Keep health, financial and household records private. Use synthetic examples in this public repo, never real prescriptions, statements, addresses or eligibility documents.
- Distinguish projected savings from realized savings, and count fees, lost benefits and the cost of switching.
- Recurring price checks, deadline tracking and new external-service integrations need their own design and permission; this note does not add them to the current app.
