# Retail Banking Sentiment Analysis Dashboard

A fully functional Streamlit prototype that analyses South African retail banking customer feedback — Banking App, Instant EFT, Branch, and Card/ATM — and turns it into KPIs, interactive charts, an executive insights report, and a downloadable results file.

**Live dashboard:** https://tshepisofrominnostation.github.io/banking-sentiment-dashboard/

Two ways to look at it:
- **Published dashboard (live, no setup):** real TextBlob scores for all four datasets, interactive filters, trend and segment analysis.
- **Streamlit app (local, full pipeline):** `streamlit run app.py` for CSV upload and the executive report.

## Headline findings (recomputed 2026-10-29)

| Dataset | Reviews | Negative | Avg polarity |
|---|---|---|---|
| Baseline sample (Sep 2026) | 41 | 51.2% | -0.108 |
| March baseline | 40 | 47.5% | +0.007 |
| June improved | 40 | **27.5%** | +0.148 |
| November incident | 40 | **45.0%** | +0.010 |

- **Banking App is the weakest channel: 61.5% negative.** Branch is the strongest at 33.3%.
- **Young Professionals (71.4%) and Families (70.0%) carry the most negative sentiment;** Small Business the least (25.0%).
- The same instrument tracks events: an app fix dropped negativity 20 points (March to June), and an incident pushed it back 17.5 points (June to November).
- Scores are computed in Python (`polish_analyze.py`) and exported to `docs/data.json`; the dashboard renders those numbers, so the page shows real TextBlob output rather than an approximation.

## What it does

1. **Ingests data** — a bundled 41-row SA retail banking sample dataset, or your own CSV (`Review_ID, Date, Channel, Review_Text, Customer_Segment`)
2. **Preprocesses text** — lowercasing, URL removal, special-character stripping (`re` pipeline)
3. **Scores sentiment** — TextBlob polarity (-1.0 to +1.0) and subjectivity, categorised as Positive (> +0.1), Neutral (-0.1 to +0.1), Negative (< -0.1)
4. **Visualises** — KPI metrics row, sentiment donut chart, channel × sentiment grouped bar chart (Plotly)
5. **Filters** — sidebar Channel and Sentiment filters over the whole dashboard
6. **Exports** — processed results download as CSV
7. **Reports** — an auto-generated Executive Business Report: ranked drivers of negative sentiment (app stability & outages, fees, payment delays, fraud, service, accessibility) with representative quotes, and strategic recommendations each tied to a finding and a metric to track

## Setup & run (step by step)

### 1. Clone the repository

```bash
git clone https://github.com/tshepisofrominnostation/banking-sentiment-dashboard.git
cd banking-sentiment-dashboard
```

### 2. Create a virtual environment

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the dashboard

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Upload your own data

Use the sidebar uploader. Required columns: `Review_ID`, `Date`, `Channel`, `Review_Text` (`Customer_Segment` optional). If a column is missing the app shows a clear error and falls back to the sample dataset.

## Project structure

```
banking-sentiment-dashboard/
├── app.py                    # Streamlit app — analysis engine + UI
├── data/
│   └── default_reviews.csv   # Bundled SA retail banking sample (41 rows)
├── requirements.txt          # Pinned dependencies
└── README.md
```

## Method notes

- **TextBlob PatternAnalyzer** scores polarity/subjectivity on the *original* review text (intact sentences); the cleaned text is used for theme matching.
- Thresholds: Positive > +0.1, Negative < -0.1.
- The bundled dataset is realistic sample data for prototype demonstration; swap in real feedback via the CSV uploader for production analysis.
- Known limitations: sarcasm and mixed reviews can be mislabelled by any lexicon-based scorer; Akan-language or code-switched reviews are not handled.

## Author

**Tshepiso Freddy Thosago** — BCom Information Systems (University of Johannesburg), Full Stack Software Engineering trainee at CAPACITI.

- Portfolio: https://tshepisofrominnostation.github.io/portfolio/
- GitHub: https://github.com/tshepisofrominnostation
- Email: tshepisothosago@gmail.com
