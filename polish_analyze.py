"""Polish pass: re-score all review sets with TextBlob and export dashboard data."""
import csv, json, re, collections
from pathlib import Path
from textblob import TextBlob

DATA = Path("data")
SETS = {
    "main": ("default_reviews.csv", "Baseline sample (Sep 2026)"),
    "march": ("practice_reviews_march_baseline.csv", "March baseline"),
    "june": ("practice_reviews_june_improved.csv", "June improved"),
    "november": ("practice_reviews_november_incident.csv", "November incident"),
}
STOP = set("""a an the and or but if is are was were be been being to of in on at for with from by as it its this that these those i you he she we they my your our their me us them not no so very just really too also can could would should will do does did have has had app banking bank
""".split())

def clean(t):
    t = re.sub(r"http\S+|www\.\S+", " ", str(t))
    t = re.sub(r"[^A-Za-z0-9\s'.,!?-]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def label(p):
    if p > 0.1: return "Positive"
    if p < -0.1: return "Negative"
    return "Neutral"

def score_rows(rows):
    out = []
    for r in rows:
        text = clean(r.get("Review_Text", ""))
        b = TextBlob(text)
        p, s = b.sentiment.polarity, b.sentiment.subjectivity
        out.append({
            "id": r.get("Review_ID", ""), "date": r.get("Date", ""),
            "channel": r.get("Channel", ""), "segment": r.get("Customer_Segment", ""),
            "text": r.get("Review_Text", ""), "clean": text,
            "polarity": round(p, 4), "subjectivity": round(s, 4), "sentiment": label(p),
        })
    return out

def summarise(rows):
    n = len(rows) or 1
    mix = collections.Counter(r["sentiment"] for r in rows)
    by_channel = {}
    for ch in sorted({r["channel"] for r in rows}):
        sub = [r for r in rows if r["channel"] == ch]
        neg = sum(1 for r in sub if r["sentiment"] == "Negative")
        by_channel[ch] = {"total": len(sub), "avg_polarity": round(sum(r["polarity"] for r in sub)/len(sub), 4),
                          "negative": neg, "negative_pct": round(100*neg/len(sub), 1)}
    by_seg = {}
    for sg in sorted({r["segment"] for r in rows}):
        sub = [r for r in rows if r["segment"] == sg]
        neg = sum(1 for r in sub if r["sentiment"] == "Negative")
        by_seg[sg] = {"total": len(sub), "negative_pct": round(100*neg/len(sub), 1),
                      "avg_polarity": round(sum(r["polarity"] for r in sub)/len(sub), 4)}
    words = collections.Counter()
    for r in rows:
        if r["sentiment"] == "Negative":
            for w in re.findall(r"[a-z']+", r["clean"].lower()):
                if w not in STOP and len(w) > 3: words[w] += 1
    return {"total": len(rows),
            "mix": {k: mix.get(k, 0) for k in ("Positive", "Neutral", "Negative")},
            "mix_pct": {k: round(100*mix.get(k, 0)/n, 1) for k in ("Positive", "Neutral", "Negative")},
            "avg_polarity": round(sum(r["polarity"] for r in rows)/n, 4),
            "avg_subjectivity": round(sum(r["subjectivity"] for r in rows)/n, 4),
            "negative_pct": round(100*mix.get("Negative", 0)/n, 1),
            "by_channel": by_channel, "by_segment": by_seg,
            "negative_terms": words.most_common(25)}

payload = {"generated_by": "TextBlob polarity/subjectivity, recomputed 2026-10-29", "sets": {}}
for key, (fn, label_txt) in SETS.items():
    path = DATA / fn
    if not path.exists():
        continue
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    scored = score_rows(rows)
    payload["sets"][key] = {"label": label_txt, "file": fn, "summary": summarise(scored), "reviews": scored}
    print(f"{key:9s} {label_txt:26s} n={len(scored):3d}  neg={payload['sets'][key]['summary']['negative_pct']:5.1f}%  avg polarity={payload['sets'][key]['summary']['avg_polarity']:+.3f}")

Path("docs").mkdir(exist_ok=True)
Path("docs/data.json").write_text(json.dumps(payload, indent=1))
print("\nwrote docs/data.json", round(Path("docs/data.json").stat().st_size/1024, 1), "KB")
