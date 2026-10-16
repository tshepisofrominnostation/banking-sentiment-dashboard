"""Validate practice datasets: intended label vs TextBlob classification."""
from __future__ import annotations
import csv
from textblob import TextBlob

def classify(p):
    return "P" if p > 0.1 else ("N" if p < -0.1 else "U")

INTENDED = {}
# rebuild intended from the generator module
import make_practice_sets as gen
for rows, prefix in [(gen.MARCH, "M"), (gen.JUNE, "J"), (gen.NOVEMBER, "N")]:
    for i, (_, _, _, text, label) in enumerate(rows, 1):
        INTENDED[f"{prefix}{i:03d}"] = (text, label)

for path in ["practice_reviews_march_baseline.csv",
             "practice_reviews_june_improved.csv",
             "practice_reviews_november_incident.csv"]:
    bad = 0
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rid = row["Review_ID"]
            pol = TextBlob(row["Review_Text"]).polarity
            got = classify(pol)
            want = INTENDED[rid][1]
            if got != want:
                bad += 1
                print(f"MISMATCH {rid} want={want} got={got} ({pol:+.2f}) | {row['Review_Text'][:60]}")
    print(f"{path}: {bad} mismatches")
