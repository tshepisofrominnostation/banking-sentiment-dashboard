# Practice Datasets

Three 40-row datasets with the same schema as `default_reviews.csv`. Upload them
through the dashboard's CSV uploader (sidebar). Every row was validated against
TextBlob so the intended sentiment classification holds (thresholds: +/-0.1).

| File | Month | Analytical profile |
|---|---|---|
| `practice_reviews_march_baseline.csv` | March 2026 | Complaint-heavy baseline: app crashes tied to load shedding, month-end queues, fee increases, card cloning. Introduces WhatsApp Banking and Contact Centre channels. |
| `practice_reviews_june_improved.csv` | June 2026 | Post-intervention month: app stability fixed, queues managed, new features praised. Negative share drops sharply; residual gripes are fees and legacy-phone performance. |
| `practice_reviews_november_incident.csv` | November 2026 | Incident month: a 5-day app outage (2-6 Nov), a phishing wave mid-month, and Black Friday payment stress. Heaviest negative cluster by date, offset by visible recovery goodwill. Great for spike and date-pattern analysis. |

## Suggested exercises
1. Run each set and compare the KPI row: negative % (March 47.5% -> June 27.5% -> November 45%), average polarity, and channel mix.
2. March vs June: which channel improved most after the app update? Which complaints survived the intervention (hint: fees)?
3. November: sort the data table by Date and find the outage cluster; check which channels absorbed the load (Branch, Contact Centre, WhatsApp) and which sentiment the recovery earned.
4. Upload your own export from any month and compare against these baselines.

Datasets are synthetic and hand-written for practice; they are representative of
South African retail banking feedback but are not live customer data.
