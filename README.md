# Retail Banking Sentiment Analysis Dashboard

A fully functional Streamlit prototype that analyses South African retail banking customer feedback — Banking App, Instant EFT, Branch, and Card/ATM — and turns it into KPIs, interactive charts, an executive insights report, and a downloadable results file.

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
