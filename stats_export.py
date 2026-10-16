import sys, json
sys.path.insert(0, '.')
import app
import pandas as pd

df = app.load_default_data.__wrapped__()
out = app.analyze(df)
kpis = app.kpi_snapshot(out)
themes = app.detect_themes(out)
recs = app.build_recommendations(out, themes)

ch = out.groupby('Channel').agg(Reviews=('Review_ID','count'), AvgPolarity=('Polarity','mean')).round(3)
ch['Positive'] = out[out['Sentiment']=='Positive'].groupby('Channel').size()
ch['Neutral'] = out[out['Sentiment']=='Neutral'].groupby('Channel').size()
ch['Negative'] = out[out['Sentiment']=='Negative'].groupby('Channel').size()
ch = ch.fillna(0).astype({'Positive':int,'Neutral':int,'Negative':int})
ch['NegPct'] = (100*ch.Negative/ch.Reviews).round(1)
ch['PosPct'] = (100*ch.Positive/ch.Reviews).round(1)
ch = ch.sort_values('NegPct', ascending=False)
print("=== CHANNEL COMPARISON ===")
print(ch.to_string())

seg = out.groupby('Customer_Segment').agg(Reviews=('Review_ID','count'), AvgPolarity=('Polarity','mean')).round(3)
seg['Negative'] = out[out['Sentiment']=='Negative'].groupby('Customer_Segment').size().fillna(0).astype(int)
seg['NegPct'] = (100*seg.Negative/seg.Reviews).round(1)
seg = seg.sort_values('NegPct', ascending=False)
print("\n=== SEGMENT COMPARISON ===")
print(seg.to_string())

print("\n=== KPIs ===")
print(kpis)
print("\n=== THEMES ===")
for t in themes: print(t['theme'], t['count'], t['share'], '|', t['quote'][:65])
print("\n=== RECS ===")
for r in recs: print('-', r['finding'][:95], '->', r['action'][:70], '| metric:', r['metric'])

neg = out.nsmallest(4, 'Polarity')[['Review_ID','Channel','Review_Text','Polarity']]
print("\n=== MOST NEGATIVE ===")
for r in neg.itertuples(): print(r.Review_ID, r.Channel, round(r.Polarity,2), '|', r.Review_Text[:75])
pos = out.nlargest(3, 'Polarity')[['Review_ID','Channel','Review_Text','Polarity']]
print("\n=== MOST POSITIVE ===")
for r in pos.itertuples(): print(r.Review_ID, r.Channel, round(r.Polarity,2), '|', r.Review_Text[:75])

# polarity by channel for chart export
ch2 = ch.reset_index()[['Channel','Reviews','Positive','Neutral','Negative','NegPct','PosPct','AvgPolarity']]
ch2.to_json('/tmp/banking_channel.json', orient='records')
json.dump(kpis, open('/tmp/banking_kpis.json','w'))
json.dump(themes, open('/tmp/banking_themes.json','w'), default=str)
seg.reset_index().to_json('/tmp/banking_seg.json', orient='records')
