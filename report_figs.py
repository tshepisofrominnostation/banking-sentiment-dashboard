"""Generate report figures from the real dashboard analysis (matplotlib)."""
import sys
import pandas as pd
sys.path.insert(0, '.')
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import app

NAVY = "#0a1628"
PANEL = "#0f2038"
GRID = "#22395c"
TEXT = "#c9d6e8"
POS, NEG, NEU = "#22c55e", "#ef4444", "#64748b"
CYAN = "#22d3ee"

df = app.load_default_data.__wrapped__()
out = app.analyze(df)

plt.rcParams.update({
    "figure.facecolor": NAVY, "axes.facecolor": NAVY,
    "axes.edgecolor": GRID, "axes.labelcolor": TEXT,
    "text.color": TEXT, "xtick.color": TEXT, "ytick.color": TEXT,
    "font.size": 9, "grid.color": GRID,
})

# ── Fig 1: sentiment donut ─────────────────────────────
counts = out["Sentiment"].value_counts()
vals = [counts.get("Positive", 0), counts.get("Neutral", 0), counts.get("Negative", 0)]
fig, ax = plt.subplots(figsize=(5.2, 3.4))
w, _ = ax.pie(vals, colors=[POS, NEU, NEG], startangle=90, counterclock=False,
              wedgeprops=dict(width=0.42, edgecolor=NAVY, linewidth=2))
ax.text(0, 0.06, f"{len(out)}", ha="center", va="center", fontsize=22, fontweight="bold", color="white")
ax.text(0, -0.22, "reviews", ha="center", va="center", fontsize=9, color=TEXT)
ax.legend(w, [f"Positive  {vals[0]}  ({vals[0]/len(out)*100:.1f}%)",
              f"Neutral   {vals[1]}  ({vals[1]/len(out)*100:.1f}%)",
              f"Negative  {vals[2]}  ({vals[2]/len(out)*100:.1f}%)"],
          loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=9)
ax.set_title("Overall sentiment distribution", color="white", fontsize=11, fontweight="bold")
plt.tight_layout(); plt.savefig("reports/fig_sentiment_donut.png", dpi=150, facecolor=NAVY); plt.close()

# ── Fig 2: channel × sentiment stacked bars ────────────
ct = pd.crosstab(out["Channel"], out["Sentiment"]).reindex(columns=["Positive", "Neutral", "Negative"]).fillna(0)
order = ct.assign(t=ct.sum(axis=1)).sort_values("t", ascending=False).index
ct = ct.loc[order]
fig, ax = plt.subplots(figsize=(6.4, 3.4))
x = range(len(ct))
b1 = ax.bar(x, ct["Positive"], color=POS, label="Positive")
b2 = ax.bar(x, ct["Neutral"], bottom=ct["Positive"], color=NEU, label="Neutral")
b3 = ax.bar(x, ct["Negative"], bottom=ct["Positive"] + ct["Neutral"], color=NEG, label="Negative")
for i, ch in enumerate(ct.index):
    ax.text(i, ct.loc[ch].sum() + 0.35, f"{int(ct.loc[ch].sum())}", ha="center", fontsize=9, color=TEXT)
ax.set_xticks(list(x)); ax.set_xticklabels(ct.index, fontsize=9)
ax.set_ylabel("Reviews")
ax.set_title("Review volume and sentiment mix by banking channel", color="white", fontsize=11, fontweight="bold")
ax.legend(frameon=False, fontsize=9, loc="upper right")
ax.grid(axis="y", alpha=0.3)
plt.tight_layout(); plt.savefig("reports/fig_channel_mix.png", dpi=150, facecolor=NAVY); plt.close()

# ── Fig 3: negative % + avg polarity comparison ────────
neg_pct = (ct["Negative"] / ct.sum(axis=1) * 100).sort_values(ascending=False)
avg_pol = out.groupby("Channel")["Polarity"].mean().round(3)
fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.2))
axes[0].barh(list(neg_pct.index)[::-1], list(neg_pct.values)[::-1], color=NEG, height=0.55)
for i, v in enumerate(list(neg_pct.values)[::-1]):
    axes[0].text(v + 1.5, i, f"{v:.1f}%", va="center", fontsize=9, color=TEXT)
axes[0].set_title("Negative reviews per channel (%)", color="white", fontsize=10, fontweight="bold")
axes[0].set_xlim(0, 78); axes[0].grid(axis="x", alpha=0.3)
ap = avg_pol.loc[neg_pct.index]
axes[1].barh(list(ap.index)[::-1], list(ap.values)[::-1],
             color=[NEG if v < 0 else POS for v in list(ap.values)[::-1]], height=0.55)
for i, v in enumerate(list(ap.values)[::-1]):
    axes[1].text(v + (0.012 if v >= 0 else -0.012), i, f"{v:+.3f}", va="center",
                 ha="left" if v >= 0 else "right", fontsize=9, color=TEXT)
axes[1].axvline(0, color=GRID, lw=1)
axes[1].set_title("Average polarity by channel", color="white", fontsize=10, fontweight="bold")
axes[1].set_xlim(-0.32, 0.12); axes[1].grid(axis="x", alpha=0.3)
plt.tight_layout(); plt.savefig("reports/fig_channel_compare.png", dpi=150, facecolor=NAVY); plt.close()

# ── Fig 4: negative drivers ranked ─────────────────────
themes = app.detect_themes(out)
names = [t["theme"] for t in themes][::-1]
counts_t = [t["count"] for t in themes][::-1]
fig, ax = plt.subplots(figsize=(6.8, 3.0))
ax.barh(names, counts_t, color=CYAN, height=0.55)
for i, v in enumerate(counts_t):
    share = v / 21 * 100
    ax.text(v + 0.08, i, f"{v} reviews ({share:.0f}% of negative)", va="center", fontsize=9, color=TEXT)
ax.set_xlim(0, 8.2)
ax.set_title("Ranked drivers of negative sentiment", color="white", fontsize=11, fontweight="bold")
ax.grid(axis="x", alpha=0.3)
plt.tight_layout(); plt.savefig("reports/fig_drivers.png", dpi=150, facecolor=NAVY); plt.close()

# ── Fig 5: customer segment comparison ─────────────────
seg = out.groupby("Customer_Segment").agg(n=("Review_ID", "count"), pol=("Polarity", "mean"))
neg_by_seg = out[out["Sentiment"] == "Negative"].groupby("Customer_Segment").size()
seg["neg"] = neg_by_seg.reindex(seg.index).fillna(0).astype(int)
seg["negpct"] = (100 * seg["neg"] / seg["n"]).round(1)
seg = seg.sort_values("negpct", ascending=False)
fig, ax = plt.subplots(figsize=(6.8, 3.0))
ax.barh(list(seg.index)[::-1], list(seg["negpct"])[::-1],
        color=[NEG if v >= 50 else "#94a3b8" for v in list(seg["negpct"])[::-1]], height=0.55)
for i, (v, n) in enumerate(zip(list(seg["negpct"])[::-1], list(seg["n"])[::-1])):
    ax.text(v + 1.5, i, f"{v:.0f}%  (n={n})", va="center", fontsize=9, color=TEXT)
ax.set_xlim(0, 100)
ax.set_title("Negative sentiment share by customer segment", color="white", fontsize=11, fontweight="bold")
ax.grid(axis="x", alpha=0.3)
plt.tight_layout(); plt.savefig("reports/fig_segments.png", dpi=150, facecolor=NAVY); plt.close()

print("figures written")
