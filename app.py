"""Retail Banking Sentiment Analysis Dashboard — South African banking sector.

A Streamlit prototype that ingests retail banking customer reviews (bundled
sample dataset or CSV upload), runs a TextBlob sentiment engine, and presents
KPIs, interactive charts, a styled data table, an executive insights report,
and CSV export of the processed results.

Run locally:
    streamlit run app.py

Author: Tshepiso Freddy Thosago
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from textblob import TextBlob

# ── Configuration ────────────────────────────────────────────────────────────

POSITIVE_THRESHOLD = 0.1      # Polarity >  0.1  -> Positive
NEGATIVE_THRESHOLD = -0.1     # Polarity < -0.1  -> Negative

DEFAULT_CSV = Path(__file__).parent / "data" / "default_reviews.csv"

SENTIMENT_COLORS = {
    "Positive": "#22c55e",
    "Neutral": "#94a3b8",
    "Negative": "#ef4444",
}

# Theme buckets used by the executive insights engine: each theme maps to
# keywords that are searched in the *preprocessed* (lowercased, cleaned)
# review text of negative reviews.
THEME_KEYWORDS: dict[str, list[str]] = {
    "App stability & outages": [
        "crash", "crashed", "crashing", "outage", "app down", "froze",
        "frozen", "logged me out", "update",
    ],
    "Fees & charges": [
        "fee", "fees", "charge", "charged", "cost", "increased",
        "sneaky", "dishonest",
    ],
    "Payment delays & limits": [
        "delay", "delayed", "pending", "limit", "cleared monday",
        "split transfers", "messed up",
    ],
    "Security & fraud": [
        "cloned", "fraud", "scam", "swallowed", "kept my card",
        "rejected my card", "disappeared",
    ],
    "Service & support": [
        "queue", "queued", "tellers", "rude", "waiting", "call centre",
        "security guard", "apology",
    ],
    "Accessibility & UX": [
        "small text", "confusing", "struggle to read", "cannot find",
        "older people", "shame",
    ],
}


# ── Data ingestion ──────────────────────────────────────────────────────────

@st.cache_data
def load_default_data() -> pd.DataFrame:
    """Load the bundled South African retail banking sample dataset.

    Returns:
        DataFrame with columns Review_ID, Date, Channel, Review_Text,
        Customer_Segment.
    """
    df = pd.read_csv(DEFAULT_CSV, parse_dates=["Date"])
    return df


def load_uploaded_csv(file) -> pd.DataFrame:
    """Load a user-uploaded CSV and validate the required columns.

    Args:
        file: UploadedFile from st.file_uploader (accepts .csv, .txt).

    Returns:
        DataFrame with the raw review rows.

    Raises:
        ValueError: if required columns are missing.
    """
    df = pd.read_csv(file)
    required = {"Review_ID", "Date", "Channel", "Review_Text"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            "Uploaded CSV is missing required column(s): "
            + ", ".join(sorted(missing))
        )
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df


# ── Preprocessing pipeline ────────────────────────────────────────────────────

_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_SPECIAL_RE = re.compile(r"[^a-z0-9\s']")
_SPACES_RE = re.compile(r"\s+")


def preprocess_text(text: str) -> str:
    """Clean a review for analysis: lowercase, strip URLs & special chars.

    Note: the *original* casing/punctuation is preserved for TextBlob scoring
    (TextBlob's analyzer benefits from intact sentences); the cleaned text is
    used for theme matching and display of processed output.
    """
    if not isinstance(text, str):
        return ""
    text = _URL_RE.sub(" ", text.lower())
    text = _SPECIAL_RE.sub(" ", text)
    return _SPACES_RE.sub(" ", text).strip()


# ── Sentiment engine (TextBlob) ──────────────────────────────────────────────

def classify_sentiment(polarity: float) -> str:
    """Map a TextBlob polarity score to a sentiment label.

    Positive if polarity > +0.1, Negative if < -0.1, otherwise Neutral.
    """
    if polarity > POSITIVE_THRESHOLD:
        return "Positive"
    if polarity < NEGATIVE_THRESHOLD:
        return "Negative"
    return "Neutral"


def analyze(df: pd.DataFrame) -> pd.DataFrame:
    """Run the sentiment engine over a raw reviews DataFrame.

    Adds: Polarity, Subjectivity, Sentiment, Clean_Text, Review_Length.
    Rows with empty review text are dropped.
    """
    df = df.copy()
    df = df[df["Review_Text"].notna()].copy()
    df = df[df["Review_Text"].astype(str).str.strip() != ""]
    df["Clean_Text"] = df["Review_Text"].apply(preprocess_text)
    blobs = df["Review_Text"].astype(str).apply(TextBlob)
    df["Polarity"] = blobs.apply(lambda b: round(b.sentiment.polarity, 3))
    df["Subjectivity"] = blobs.apply(lambda b: round(b.sentiment.subjectivity, 3))
    df["Sentiment"] = df["Polarity"].apply(classify_sentiment)
    df["Review_Length"] = df["Clean_Text"].str.split().str.len()
    return df


# ── Aggregations ─────────────────────────────────────────────────────────────

def sentiment_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame of Sentiment -> review count."""
    counts = df["Sentiment"].value_counts().reindex(
        ["Positive", "Neutral", "Negative"]
    ).fillna(0).astype(int)
    return counts.rename_axis("Sentiment").reset_index(name="Reviews")


def channel_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Return review counts grouped by Channel and Sentiment."""
    grouped = (
        df.groupby(["Channel", "Sentiment"]).size().reset_index(name="Reviews")
    )
    return grouped


def kpi_snapshot(df: pd.DataFrame) -> dict:
    """Compute the headline KPIs for the metrics row."""
    total = len(df)
    if total == 0:
        return {"total": 0, "pos_pct": 0.0, "neg_pct": 0.0, "avg_polarity": 0.0}
    pos_pct = 100 * (df["Sentiment"] == "Positive").mean()
    neg_pct = 100 * (df["Sentiment"] == "Negative").mean()
    avg_polarity = float(df["Polarity"].mean())
    return {
        "total": total,
        "pos_pct": round(pos_pct, 1),
        "neg_pct": round(neg_pct, 1),
        "avg_polarity": round(avg_polarity, 3),
    }


# ── Executive insights engine ────────────────────────────────────────────────

def detect_themes(df: pd.DataFrame) -> list[dict]:
    """Identify recurring drivers behind negative sentiment.

    Scans the cleaned text of negative reviews for theme keywords and returns
    themes sorted by frequency: name, count, share of negative reviews, and
    one representative quote.
    """
    negatives = df[df["Sentiment"] == "Negative"]
    n_neg = len(negatives)
    if n_neg == 0:
        return []
    themes = []
    for theme, keywords in THEME_KEYWORDS.items():
        mask = negatives["Clean_Text"].apply(
            lambda t: any(k in t for k in keywords)
        )
        hits = negatives[mask]
        if len(hits) > 0:
            worst = hits.sort_values("Polarity").iloc[0]
            themes.append({
                "theme": theme,
                "count": int(len(hits)),
                "share": round(100 * len(hits) / n_neg, 1),
                "quote": str(worst["Review_Text"]),
                "quote_id": str(worst["Review_ID"]),
            })
    return sorted(themes, key=lambda t: t["count"], reverse=True)


def build_recommendations(df: pd.DataFrame, themes: list[dict]) -> list[dict]:
    """Turn detected themes into strategic recommendations for bank ops.

    Each recommendation states the finding it comes from, the action, and the
    metric to track. Recommendations are derived from this dataset only.
    """
    recs: list[dict] = []
    theme_names = {t["theme"] for t in themes}

    # Worst channel by negative share (only when there are negatives).
    negatives = df[df["Sentiment"] == "Negative"]
    if len(negatives) > 0:
        per_channel = df.groupby("Channel")["Sentiment"].apply(
            lambda s: 100 * (s == "Negative").mean()
        ).sort_values(ascending=False)
        worst_channel = str(per_channel.index[0])
        worst_pct = round(float(per_channel.iloc[0]), 1)
        recs.append({
            "finding": (
                f"{worst_channel} is the weakest channel with {worst_pct}% "
                "of its reviews negative."
            ),
            "action": (
                f"Stand up a joint tech-and-ops task force to triage "
                f"{worst_channel.lower()} complaints first, with a weekly "
                "review until the negative share falls below the "
                "portfolio average."
            ),
            "metric": f"% negative {worst_channel} reviews (weekly)",
        })

    for t in themes[:3]:
        if t["theme"] == "App stability & outages":
            recs.append({
                "finding": (
                    f"App stability drives {t['count']} of "
                    f"{int((df['Sentiment'] == 'Negative').sum())} negative "
                    f"reviews ({t['share']}%), with crashes tied to load "
                    "shedding windows."
                ),
                "action": (
                    "Add load-shedding resilience testing to the release "
                    "cycle and publish an app status page; schedule deploys "
                    "outside Stage 4+ windows."
                ),
                "metric": "App crash complaints per 1,000 active users",
            })
        elif t["theme"] == "Fees & charges":
            recs.append({
                "finding": (
                    f"Fee concerns appear in {t['count']} negative reviews "
                    f"({t['share']}%), often about unexpected increases."
                ),
                "action": (
                    "Send proactive fee-change notifications 30 days ahead "
                    "and add a plain-language fee summary in-app."
                ),
                "metric": "Fee-related complaints per month",
            })
        elif t["theme"] == "Payment delays & limits":
            recs.append({
                "finding": (
                    f"Payment delays and low EFT limits appear in "
                    f"{t['count']} negative reviews ({t['share']}%)."
                ),
                "action": (
                    "Clear the overnight EFT backlog with a same-day SLA and "
                    "let customers request limit increases in-app."
                ),
                "metric": "Median EFT settlement time (hours)",
            })
        elif t["theme"] == "Security & fraud":
            recs.append({
                "finding": (
                    f"Card fraud and ATM incidents appear in {t['count']} "
                    f"negative reviews ({t['share']}%)."
                ),
                "action": (
                    "Prioritise ATM anti-skimming rollouts and introduce "
                    "real-time transaction alerts with one-tap card freeze."
                ),
                "metric": "Fraud complaints per month",
            })
        elif t["theme"] == "Service & support":
            recs.append({
                "finding": (
                    f"Branch queues and slow support appear in {t['count']} "
                    f"negative reviews ({t['share']}%), peaking at month end."
                ),
                "action": (
                    "Rota extra tellers for month-end weeks and offer "
                    "booked branch slots to pensioners."
                ),
                "metric": "Average month-end branch queue time",
            })
        elif t["theme"] == "Accessibility & UX":
            recs.append({
                "finding": (
                    f"Accessibility complaints appear in {t['count']} "
                    f"negative reviews ({t['share']}%), mainly from "
                    "pensioner customers."
                ),
                "action": (
                    "Ship a large-text/simple mode in the app and keep a "
                    "branch-assisted channel for customers who opt out."
                ),
                "metric": "Accessibility complaints per release",
            })
    if not recs:
        recs.append({
            "finding": "No negative reviews in the current selection.",
            "action": "Maintain current service levels and keep monitoring.",
            "metric": "% negative reviews (weekly)",
        })
    return recs


# ── Styling & export ─────────────────────────────────────────────────────────

def style_table(df: pd.DataFrame) -> pd.Styler:
    """Color-highlight sentiment tags in the processed data table."""
    styler = df.style.map(
        lambda v: f"background-color: {SENTIMENT_COLORS[v]}20; color: "
                  f"{SENTIMENT_COLORS[v]}; font-weight: 600",
        subset=["Sentiment"],
    )
    return styler.format({"Polarity": "{:+.2f}", "Subjectivity": "{:.2f}"})


def to_csv_bytes(df: pd.DataFrame) -> str:
    """Serialize the processed results for the download button."""
    return df.to_csv(index=False).encode("utf-8")


# ── Charts ───────────────────────────────────────────────────────────────────

def sentiment_donut(dist: pd.DataFrame):
    """Interactive donut chart of the overall sentiment distribution."""
    fig = px.pie(
        dist,
        values="Reviews",
        names="Sentiment",
        hole=0.55,
        title="Overall Sentiment Distribution",
        color="Sentiment",
        color_discrete_map=SENTIMENT_COLORS,
    )
    fig.update_traces(textinfo="value+percent", textposition="outside")
    fig.update_layout(
        legend_title_text="Sentiment",
        margin=dict(t=60, l=10, r=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def channel_bar(breakdown: pd.DataFrame):
    """Bar chart of sentiment breakdown per banking channel."""
    fig = px.bar(
        breakdown,
        x="Channel",
        y="Reviews",
        color="Sentiment",
        color_discrete_map=SENTIMENT_COLORS,
        title="Sentiment Breakdown by Banking Channel",
        barmode="group",
        category_orders={"Sentiment": ["Positive", "Neutral", "Negative"]},
    )
    fig.update_layout(
        xaxis_title="Banking Channel",
        yaxis_title="Number of Reviews",
        legend_title_text="Sentiment",
        margin=dict(t=60, l=10, r=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ── Main UI ──────────────────────────────────────────────────────────────────

def main() -> None:
    """Streamlit entry point — UI wiring only."""
    st.set_page_config(
        page_title="Retail Banking Sentiment Dashboard",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("Retail Banking Sentiment Analysis Dashboard")
    st.caption(
        "South African retail banking · TextBlob sentiment engine · "
        "Built with Streamlit"
    )

    # ── Sidebar: ingestion & filters ────────────────────────────────────
    with st.sidebar:
        st.header("Data & Filters")
        uploaded = st.file_uploader(
            "Upload your own reviews (CSV)",
            type=["csv"],
            help="Required columns: Review_ID, Date, Channel, Review_Text "
                 "(Customer_Segment optional).",
        )
        if uploaded is not None:
            try:
                raw = load_uploaded_csv(uploaded)
                st.success(f"Loaded {len(raw)} reviews from your CSV.")
            except ValueError as exc:
                st.error(str(exc))
                st.info("Falling back to the bundled sample dataset.")
                raw = load_default_data()
        else:
            raw = load_default_data()
            st.info("Using the bundled SA banking sample dataset (41 rows).")

        st.divider()

        df_all = analyze(raw)
        channels = sorted(df_all["Channel"].unique().tolist())
        sel_channels = st.multiselect(
            "Channel", channels, default=channels
        )
        sentiments = ["Positive", "Neutral", "Negative"]
        sel_sentiments = st.multiselect(
            "Sentiment", sentiments, default=sentiments
        )

    # ── Filters ─────────────────────────────────────────────────────────
    df = df_all[
        df_all["Channel"].isin(sel_channels)
        & df_all["Sentiment"].isin(sel_sentiments)
    ]
    if df.empty:
        st.warning(
            "No reviews match the current filters. Adjust the sidebar "
            "selections to see results."
        )
        return

    # ── KPI row ──────────────────────────────────────────────────────────
    kpis = kpi_snapshot(df)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Reviews", kpis["total"])
    col2.metric("% Positive", f"{kpis['pos_pct']:.1f}%")
    col3.metric("% Negative", f"{kpis['neg_pct']:.1f}%")
    col4.metric("Avg Polarity", f"{kpis['avg_polarity']:+.2f}",
                help="TextBlob polarity from -1.0 (most negative) to +1.0 "
                     "(most positive).")

    # ── Charts ───────────────────────────────────────────────────────────
    left, right = st.columns([2, 3])
    with left:
        st.plotly_chart(
            sentiment_donut(sentiment_distribution(df)),
            use_container_width=True,
        )
    with right:
        st.plotly_chart(
            channel_bar(channel_breakdown(df)),
            use_container_width=True,
        )

    # ── Data table + export ─────────────────────────────────────────────
    st.subheader("Processed Review Data")
    st.dataframe(
        style_table(df[[
            "Review_ID", "Date", "Channel", "Customer_Segment",
            "Review_Text", "Clean_Text", "Polarity", "Subjectivity",
            "Sentiment",
        ]]),
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        "Download processed results (CSV)",
        data=to_csv_bytes(df),
        file_name="sentiment_analysis_results.csv",
        mime="text/csv",
    )

    # ── Executive insights ───────────────────────────────────────────────
    st.divider()
    st.subheader("Executive Business Report")
    with st.spinner("Compiling insights..."):
        themes = detect_themes(df)

    n_neg = int((df["Sentiment"] == "Negative").sum())
    if n_neg == 0:
        st.success(
            "No negative sentiment in the current selection — nothing to "
            "escalate this period."
        )
        return

    worst_row = df.sort_values("Polarity").iloc[0]
    st.markdown(
        f"**Summary.** {kpis['total']} reviews analysed across "
        f"{df['Channel'].nunique()} channels. Negative sentiment accounts "
        f"for **{kpis['neg_pct']:.1f}%** of reviews, with the single most "
        f"negative experience "
        f"(*{worst_row['Review_Text'][:120]}*) reported via "
        f"{worst_row['Channel']}."
    )

    st.markdown("#### Key drivers of negative sentiment")
    for t in themes:
        st.markdown(
            f"**{t['theme']}** — {t['count']} review(s), "
            f"{t['share']}% of negative feedback"
        )
        st.markdown(
            f"> “{t['quote']}” — *{t['quote_id']}*"
        )

    st.markdown("#### Strategic recommendations")
    recs = build_recommendations(df, themes)
    for i, rec in enumerate(recs, 1):
        st.markdown(f"**{i}. {rec['action']}**")
        st.markdown(f"- **Finding:** {rec['finding']}")
        st.markdown(f"- **Metric to track:** {rec['metric']}")


if __name__ == "__main__":
    main()
