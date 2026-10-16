"""Generate three 40-row practice datasets for the banking sentiment dashboard.

Each set has the same schema as data/default_reviews.csv so it can be uploaded
directly through the dashboard's CSV uploader. Rows are hand-written with an
intended sentiment label (P/N/U = Positive/Negative/Neutral); validate_sets.py
checks each row against TextBlob so classification behaves as intended.

Sets:
  practice_reviews_march_baseline.csv   - complaint-heavy baseline month
  practice_reviews_june_improved.csv    - post-intervention month (app fixed)
  practice_reviews_november_incident.csv - outage-incident month (spike practice)
"""
from __future__ import annotations

import csv
from pathlib import Path

APP, EFT, BR, ATM = "Banking App", "Instant EFT", "Branch", "Card/ATM"
WA, CC = "WhatsApp Banking", "Contact Centre"
ST, YP, FA, SB, PE = "Student", "Young Professional", "Family", "Small Business", "Pensioner"

MARCH = [
    ("2026-03-02", APP, YP, "The app keeps crashing whenever load shedding hits. So frustrating.", "N"),
    ("2026-03-03", EFT, ST, "Sent money to my flatmate and it reflected instantly. Excellent.", "P"),
    ("2026-03-05", BR, PE, "The consultant helped me order a new bank card in ten minutes. Great service.", "P"),
    ("2026-03-06", ATM, FA, "The ATM at the mall kept my card on payday. Absolutely disgusting.", "N"),
    ("2026-03-09", APP, SB, "Monthly fees went up with no warning at all. I am so disappointed.", "N"),
    ("2026-03-10", EFT, YP, "My EFT to a supplier sat pending for two days. Terrible for my business.", "N"),
    ("2026-03-12", BR, FA, "Month-end queue was out the door but the tellers were friendly and fast.", "P"),
    ("2026-03-13", ATM, ST, "Withdrew R200 for the week. The machine was out of R10 notes.", "U"),
    ("2026-03-16", APP, YP, "Biometric login works every time now. Smooth and quick.", "P"),
    ("2026-03-17", EFT, SB, "Instant EFT limit is too low for my payroll. Very annoying.", "N"),
    ("2026-03-19", BR, PE, "I waited 40 minutes just to withdraw my pension. Terrible experience.", "N"),
    ("2026-03-20", ATM, FA, "Cardless cash withdrawal at the ATM worked perfectly. Love this feature.", "P"),
    ("2026-03-23", APP, ST, "The app logged me out twice while paying for data. Frustrating.", "N"),
    ("2026-03-24", EFT, FA, "Paid the school fees online, cleared same day. Easy and painless.", "P"),
    ("2026-03-26", BR, SB, "Opened my business account in one visit. The consultant was brilliant.", "P"),
    ("2026-03-27", ATM, YP, "ATM was out of cash the whole weekend. Had to drive to three machines, terrible.", "N"),
    ("2026-03-30", APP, FA, "App down again during stage 4 load shedding. Third time this month, awful.", "N"),
    ("2026-03-31", BR, PE, "Queue on grant day was long but the security guard helped us, very kind.", "P"),
    ("2026-03-03", EFT, YP, "Payment to my car dealer reflected in seconds. Fantastic.", "P"),
    ("2026-03-07", APP, SB, "Cannot upload invoices on the app. Useless for business banking.", "N"),
    ("2026-03-11", ATM, ST, "My card was cloned at a sketchy ATM. I am so angry about this.", "N"),
    ("2026-03-14", BR, FA, "The branch closed early without notice. Wasted trip, very annoying.", "N"),
    ("2026-03-18", EFT, SB, "Batch payments cleared overnight without any issues. Great work.", "P"),
    ("2026-03-21", APP, PE, "The font on the app is too small for me. Struggled to read my balance.", "N"),
    ("2026-03-25", ATM, FA, "Withdrew cash for the weekend braai, no issues at all.", "U"),
    ("2026-03-28", APP, ST, "Notifications for every swipe are so helpful for budgeting. Love it.", "P"),
    ("2026-03-31", BR, SB, "Tellers could not process my deposit slip properly. Disappointed with the service.", "N"),
    ("2026-03-05", CC, YP, "Called the contact centre and the agent sorted my dispute in one call. Excellent.", "P"),
    ("2026-03-08", CC, FA, "Held for 25 minutes on the phone then got cut off. Disgusting.", "N"),
    ("2026-03-15", CC, PE, "The lady on the phone was patient, kind and brilliant with my reversal. Excellent service.", "P"),
    ("2026-03-22", CC, SB, "Nobody at the contact centre understands merchant codes. Useless.", "N"),
    ("2026-03-04", WA, YP, "WhatsApp banking answered my balance query in seconds. Impressive.", "P"),
    ("2026-03-10", WA, ST, "The WhatsApp chatbot kept looping the same menu. So frustrating.", "N"),
    ("2026-03-19", WA, FA, "Blocked my lost card through WhatsApp in two minutes. Brilliant.", "P"),
    ("2026-03-26", WA, PE, "I do not understand the WhatsApp banking prompts. Confusing for me.", "N"),
    ("2026-03-12", ATM, SB, "Deposited my weekend takings at the ATM. Receipt printed and done.", "U"),
    ("2026-03-17", EFT, ST, "My transfer to myself took two days to clear. Annoying.", "N"),
    ("2026-03-24", APP, FA, "The new statements view is clean and easy to read. Great improvement.", "P"),
    ("2026-03-29", BR, YP, "Branch consultant opened my tax-free savings account quickly. Happy with the service.", "P"),
    ("2026-03-16", EFT, PE, "Moved R500 from my current account to my savings at the teller.", "U"),
]

JUNE = [
    ("2026-06-01", APP, YP, "The app update fixed all the crashing. Excellent and rock solid during load shedding now.", "P"),
    ("2026-06-02", EFT, ST, "Instant EFT cleared in seconds again. Excellent as always.", "P"),
    ("2026-06-03", BR, PE, "New queue system at the branch meant ten minutes max. Impressed.", "P"),
    ("2026-06-04", ATM, FA, "Cardless withdrawal with my phone worked first time. Love it.", "P"),
    ("2026-06-05", APP, SB, "Still getting charged for notice deposits. Fees are disappointing.", "N"),
    ("2026-06-08", EFT, SB, "Payroll EFT batch processed same day. Smooth and reliable.", "P"),
    ("2026-06-09", ATM, YP, "ATM was out of service for maintenance on payday. Very annoying.", "N"),
    ("2026-06-10", BR, FA, "Teller helped reverse a double debit order with a smile. Great service.", "P"),
    ("2026-06-11", APP, ST, "The app now lets me freeze my card instantly. Fantastic feature.", "P"),
    ("2026-06-12", EFT, YP, "My transfer was delayed overnight. Still not happy about that.", "N"),
    ("2026-06-15", WA, YP, "WhatsApp banking handled my beneficiary payment end to end. Brilliant.", "P"),
    ("2026-06-16", BR, PE, "Youth Day crowd was big but staff kept the queue moving. Impressive.", "P"),
    ("2026-06-17", ATM, ST, "Withdrew R300 for the long weekend at the campus ATM.", "U"),
    ("2026-06-18", APP, FA, "App performance on old phones is still slow. Frustrating for my mother.", "N"),
    ("2026-06-19", CC, SB, "Merchant support call resolved in eight minutes. Excellent.", "P"),
    ("2026-06-22", EFT, FA, "School fee payment cleared instantly. Quick and easy.", "P"),
    ("2026-06-23", APP, PE, "The larger font option in settings is so helpful and easy. Great improvement.", "P"),
    ("2026-06-24", BR, SB, "Business account statements were wrong for a week. Disappointed.", "N"),
    ("2026-06-25", ATM, FA, "Cash deposit machine rejected four of my notes. Very annoying.", "N"),
    ("2026-06-26", WA, ST, "Chatbot answered my campus card query perfectly. Love the speed.", "P"),
    ("2026-06-29", APP, YP, "Load shedding hit for four hours and the app never went down. Great work.", "P"),
    ("2026-06-30", BR, PE, "Grant day queue was managed so well this month. Excellent.", "P"),
    ("2026-06-05", CC, FA, "Called about a suspicious debit and got help immediately. Impressed.", "P"),
    ("2026-06-08", EFT, ST, "My shared flat electricity payment bounced twice. Terrible.", "N"),
    ("2026-06-11", ATM, YP, "The ATM gave me R100 short but the branch fixed it same day. Happy with the fix.", "P"),
    ("2026-06-14", APP, SB, "Invoice upload finally works on the app. Great improvement for business.", "P"),
    ("2026-06-16", WA, PE, "The WhatsApp prompts are simpler now. Easy to follow, thank you.", "P"),
    ("2026-06-18", BR, YP, "Consultant explained the new savings product clearly. Helpful.", "P"),
    ("2026-06-20", ATM, SB, "Night deposit for my shop at the branch deposit slot before closing.", "U"),
    ("2026-06-22", APP, FA, "My card was blocked by fraud systems wrongly. Very frustrating experience.", "N"),
    ("2026-06-25", EFT, SB, "Same-day settlement on the new EFT rails is fantastic.", "P"),
    ("2026-06-27", CC, PE, "Waited 15 minutes on hold about my statement. Annoying.", "N"),
    ("2026-06-02", CC, ST, "Agent reset my online banking in minutes. Great support.", "P"),
    ("2026-06-09", WA, FA, "Loaded beneficiaries on WhatsApp without any problems. Easy.", "P"),
    ("2026-06-13", BR, ST, "Branch ATM deposit window closed early. Disappointed.", "N"),
    ("2026-06-17", APP, PE, "I still struggle with the app menus. Confusing for pensioners.", "N"),
    ("2026-06-21", EFT, YP, "Split the bill with three friends instantly. Love this.", "P"),
    ("2026-06-26", ATM, FA, "Drew cash for the school cake sale at the branch ATM.", "U"),
    ("2026-06-30", APP, SB, "Month-end recon on the app took half the time. Excellent update.", "P"),
    ("2026-06-29", ATM, PE, "Withdrew my grant money at the post office ATM. Transaction completed.", "U"),
]

NOVEMBER = [
    ("2026-11-02", APP, YP, "The app has been down since Sunday. So frustrating, I cannot pay anyone.", "N"),
    ("2026-11-02", EFT, SB, "My payroll batch failed in the outage. Terrible day for my business.", "N"),
    ("2026-11-03", APP, ST, "Cannot check my balance before the outage notice even appeared. Angry.", "N"),
    ("2026-11-03", CC, FA, "Contact centre queue was 40 minutes during the outage. Disgusting.", "N"),
    ("2026-11-04", BR, PE, "The branch was packed with angry customers during the app outage.", "N"),
    ("2026-11-04", APP, YP, "Day three of the app not loading. The worst week, absolutely terrible.", "N"),
    ("2026-11-05", BR, YP, "Consultants set up paper withdrawals for everyone. Great recovery effort.", "P"),
    ("2026-11-05", CC, SB, "A supervisor called me back to fix my merchant payments. Impressed.", "P"),
    ("2026-11-06", APP, FA, "App is back and my transfers went through. Excellent recovery.", "P"),
    ("2026-11-06", EFT, FA, "Backlog of payments cleared overnight. Great work by the bank.", "P"),
    ("2026-11-09", APP, ST, "Got a phishing SMS pretending to be the bank. Scary and sneaky.", "N"),
    ("2026-11-10", EFT, PE, "Nearly fell for a fake bank WhatsApp. These scammers are terrible.", "N"),
    ("2026-11-11", APP, YP, "The in-app fraud warnings are clear and helpful. Love that.", "P"),
    ("2026-11-12", ATM, FA, "Skimming device found at our local ATM. I am so angry, feel completely unsafe there.", "N"),
    ("2026-11-13", CC, SB, "The bank froze my card after a suspicious R8,000 charge. Great security, so happy.", "P"),
    ("2026-11-16", APP, ST, "Someone tried to log in as me and the app blocked them. Great security.", "P"),
    ("2026-11-17", WA, PE, "Reported a scam number through WhatsApp banking. Quick response, impressed.", "P"),
    ("2026-11-18", EFT, YP, "Black Friday payment failed twice. Very annoying at midnight.", "N"),
    ("2026-11-19", APP, FA, "Black Friday checkout through the app was seamless. Excellent.", "P"),
    ("2026-11-20", EFT, SB, "My supplier payment was delayed on the busiest weekend. Disappointed.", "N"),
    ("2026-11-21", BR, ST, "Branch was calm and quick after the online rush. Friendly tellers.", "P"),
    ("2026-11-23", ATM, YP, "ATM limits dropped my cash withdrawal on payday. Terrible timing.", "N"),
    ("2026-11-24", APP, SB, "Stokvel payout day and the app struggled all morning. Frustrating.", "N"),
    ("2026-11-25", CC, FA, "Waited 20 minutes to dispute a Black Friday double charge. Annoying.", "N"),
    ("2026-11-26", EFT, ST, "Refund from an online store reflected the same day. Great.", "P"),
    ("2026-11-27", APP, YP, "Black Friday sale purchase went through instantly at midnight. Brilliant.", "P"),
    ("2026-11-27", EFT, FA, "My transfer to family for December took two days. Not happy.", "N"),
    ("2026-11-28", BR, PE, "Consultant helped me set up account alerts. Friendly, patient and excellent.", "P"),
    ("2026-11-29", ATM, SB, "Cash deposit for the shop counted wrong by R50. Disappointed.", "N"),
    ("2026-11-30", APP, PE, "The app kept me informed through the whole outage week. Impressed.", "P"),
    ("2026-11-08", WA, YP, "WhatsApp banking never skipped a beat during the outage. Fantastic.", "P"),
    ("2026-11-13", BR, SB, "Business banking desk sorted my POS machine issue same day. Excellent.", "P"),
    ("2026-11-14", ATM, ST, "Used the campus ATM for my allowance withdrawal. No problems.", "U"),
    ("2026-11-15", EFT, PE, "My grandchild's transfer took three days during the backlog. Frustrating.", "N"),
    ("2026-11-18", CC, PE, "The call centre agent was rude about my phishing report. Disgusted.", "N"),
    ("2026-11-20", APP, FA, "App stability since the outage has been perfect. Great to see.", "P"),
    ("2026-11-22", BR, YP, "Opened a December savings plan with good advice. Helpful consultant.", "P"),
    ("2026-11-25", ATM, FA, "Drew December grocery money at the mall ATM.", "U"),
    ("2026-11-28", EFT, SB, "Client payments all landed on time this week. Smooth sailing.", "P"),
    ("2026-11-21", WA, SB, "Checked my shop balance on WhatsApp during the outage week.", "U"),
]

def write_set(rows, path, prefix):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Review_ID", "Date", "Channel", "Review_Text", "Customer_Segment"])
        for i, (date, ch, seg, text, _label) in enumerate(rows, 1):
            w.writerow([f"{prefix}{i:03d}", date, ch, text, seg])

def main() -> None:
    out = Path(__file__).parent
    write_set(MARCH, out / "practice_reviews_march_baseline.csv", "M")
    write_set(JUNE, out / "practice_reviews_june_improved.csv", "J")
    write_set(NOVEMBER, out / "practice_reviews_november_incident.csv", "N")
    print("wrote", len(MARCH), len(JUNE), len(NOVEMBER), "rows")

if __name__ == "__main__":
    main()
