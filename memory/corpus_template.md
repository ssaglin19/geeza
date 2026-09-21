# Memory Corpus Template

Fill this out for each parent. The ingester (`ingest/ingest.py`) turns this into `memory.sqlite` for on-device retrieval.

---

## Parent: [Name]

### Daily Routine

| Time | Activity | Notes |
|------|----------|-------|
| 6:00 AM | Wake up, coffee | Takes blood pressure pill with breakfast |
| 7:00 AM | Breakfast | Oatmeal, banana, coffee |
| 8:00 AM | Morning walk | 30 minutes, same route |
| 9:00 AM | Newspaper | Reads at kitchen table |
| 10:00 AM | [Activity] | |
| 12:00 PM | Lunch | |
| 1:00 PM | Nap | 1 hour |
| 3:00 PM | [Activity] | |
| 5:00 PM | Dinner prep | |
| 6:00 PM | Dinner | |
| 7:00 PM | TV / News | Watches local news for weather |
| 9:00 PM | [Activity] | |
| 10:00 PM | Bed | |

### Weekly Routine

| Day | Activity | Notes |
|-----|----------|-------|
| Monday | [Activity] | |
| Tuesday | [Activity] | |
| Wednesday | Grocery shopping | Kroger, 10 AM |
| Thursday | [Activity] | |
| Friday | [Activity] | |
| Saturday | [Activity] | |
| Sunday | Church | 9 AM service |

### Medications

| Medication | Dose | Frequency | Time | Notes |
|------------|------|-----------|------|-------|
| Lisinopril | 10mg | Daily | 8 AM | Blood pressure |
| Metformin | 500mg | 2x daily | 8 AM, 6 PM | Diabetes |
| Atorvastatin | 20mg | Daily | Bedtime | Cholesterol |
| Vitamin D | 1000 IU | Daily | Breakfast | |
| [Med] | | | | |

### Doctors & Appointments

| Doctor | Specialty | Phone | Address | Next Appointment |
|--------|-----------|-------|---------|------------------|
| Dr. Patel | Primary Care | 555-0101 | 123 Main St | Oct 15, 2026 |
| Dr. Nguyen | Cardiology | 555-0102 | 456 Oak Ave | Nov 3, 2026 |
| [Doctor] | | | | |

### Emergency Contacts

| Name | Relationship | Phone | Notes |
|------|--------------|-------|-------|
| Sean | Son | 555-0201 | Primary contact |
| Sarah | Daughter | 555-0202 | Backup |
| Dr. Patel | Doctor | 555-0101 | After hours: 555-0103 |
| [Name] | | | |

### Family & Friends

| Name | Relationship | Phone | Birthday | Notes |
|------|--------------|-------|----------|-------|
| Sean | Son | 555-0201 | Mar 15 | Lives nearby |
| Sarah | Daughter | 555-0202 | Jul 22 | Calls weekly |
| Mike | Grandson | 555-0203 | Dec 1 | Sarah's son |
| [Name] | | | | |

### Accounts & Bills

| Account | Company | Account # | Due Date | Amount | Notes |
|---------|---------|-----------|----------|--------|-------|
| Electric | Consumers Energy | 123456789 | 15th | ~$85 | Auto-pay? |
| Gas | DTE | 987654321 | 20th | ~$45 | |
| Internet | Comcast | 456123789 | 1st | ~$75 | |
| Phone | AT&T | 789456123 | 5th | ~$60 | |
| [Account] | | | | | |

### Preferences & Notes

- **Newspaper:** [Name] delivered daily, reads front to back
- **TV:** Watches [Channel] news at 6 PM, [Show] at 8 PM
- **Food:** Likes [Food], dislikes [Food], allergic to [Food]
- **Weather:** Checks news for weather, doesn't use phone apps
- **Calendar:** Paper calendar on kitchen wall, writes everything down
- **Notes:** [Any other important notes]

### Important Dates

| Date | Event | Notes |
|------|-------|-------|
| Jan 15 | Wedding anniversary | |
| Mar 15 | Sean's birthday | |
| Jul 22 | Sarah's birthday | |
| Dec 25 | Christmas | Family dinner |
| [Date] | | |

### Medical History

- **Conditions:** Hypertension, Type 2 diabetes, high cholesterol
- **Allergies:** Penicillin
- **Surgeries:** [List]
- **Hospital:** [Preferred hospital]

### Home & Safety

- **Address:** [Full address]
- **Emergency shutoffs:** Water [location], Gas [location], Electric [location]
- **Neighbors:** [Name] at [Address], has spare key
- **Alarm code:** [Code] (if applicable)

---

## Instructions for Sean

1. **Copy this template** for each parent (Mom, Dad)
2. **Fill in what you know** — leave blanks for what you don't
3. **Review with them** — they'll fill in gaps and correct errors
4. **Save as** `memory/mom.md` and `memory/dad.md`
5. **Run the ingester** — `python ingest/ingest.py memory/ memory.sqlite`

The ingester will chunk this by headings, so the structure matters. Keep the headings as-is for consistent retrieval.