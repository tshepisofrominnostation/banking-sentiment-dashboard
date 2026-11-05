/* Citi Advisor — turns a sentiment summary into prioritised, explainable actions.
   Every recommendation carries its evidence, so a human can audit or override it.
   No model weights, no hidden scoring: deterministic rules over measured evidence. */
(function (root) {
  "use strict";

  function pct(x) { return Math.round(x * 10) / 10; }

  function summarise(rows) {
    var n = rows.length, neg = 0, pos = 0, neu = 0;
    var ch = {}, sg = {}, day = {}, terms = {};
    rows.forEach(function (r) {
      var s = r.sentiment;
      if (s === "Negative") neg++; else if (s === "Positive") pos++; else neu++;
      if (r.channel) { ch[r.channel] = ch[r.channel] || { n: 0, neg: 0 }; ch[r.channel].n++; if (s === "Negative") ch[r.channel].neg++; }
      if (r.segment) { sg[r.segment] = sg[r.segment] || { n: 0, neg: 0 }; sg[r.segment].n++; if (s === "Negative") sg[r.segment].neg++; }
      if (r.date) { var d = String(r.date).slice(0, 10); day[d] = day[d] || { n: 0, neg: 0 }; day[d].n++; if (s === "Negative") day[d].neg++; }
      if (s === "Negative") (String(r.text || "").toLowerCase().match(/[a-z']{4,}/g) || []).forEach(function (w) {
        terms[w] = (terms[w] || 0) + 1;
      });
    });
    var stop = { "this": 1, "that": 1, "with": 1, "have": 1, "been": 1, "they": 1, "will": 1, "from": 1, "your": 1, "very": 1, "just": 1, "again": 1, "could": 1, "would": 1, "there": 1, "their": 1, "about": 1, "when": 1, "what": 1, "which": 1 };
    var topTerms = Object.keys(terms).filter(function (w) { return !stop[w]; })
      .sort(function (a, b) { return terms[b] - terms[a]; }).slice(0, 6);
    return {
      n: n,
      mix: { negative: n ? pct(neg / n * 100) : 0, positive: n ? pct(pos / n * 100) : 0, neutral: n ? pct(neu / n * 100) : 0 },
      channels: ch, segments: sg, days: day, topTerms: topTerms
    };
  }

  function rate(o) { return o.n ? o.neg / o.n * 100 : 0; }

  function confidence(sampleSize, spread) {
    if (sampleSize >= 40 && spread >= 10) return { level: "High", why: sampleSize + " reviews, " + Math.round(spread) + " points above the rest" };
    if (sampleSize >= 15) return { level: "Medium", why: sampleSize + " reviews — direction is clear, magnitude is not" };
    return { level: "Low", why: "only " + sampleSize + " reviews — treat as a hypothesis to test, not a finding" };
  }
  var OWNER = [
    [/payment|card|money|eft|transfer|declin|refund/, "Payments & Cards"],
    [/app|login|otp|update|crash|freez|slow|screen/, "Digital / App team"],
    [/fee|charge|pricing|interest|cost/, "Pricing & Product"],
    [/queue|branch|staff|wait|minutes|teller|hour/, "Branch operations"],
    [/pension|payslip|salary|overtime|payroll/, "HR & Payroll"]
  ];

  function median(a) { a = a.slice().sort(function (x, y) { return x - y; }); var m = Math.floor(a.length / 2); return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2; }

  function advise(S) {
    var out = [];
    var channels = Object.keys(S.channels).filter(function (k) { return S.channels[k].n >= 6; });
    var segs = Object.keys(S.segments).filter(function (k) { return S.segments[k].n >= 4; });

    if (channels.length >= 2) {
      var rates = channels.map(function (k) { return rate(S.channels[k]); });
      var med = median(rates);
      var worst = channels.slice().sort(function (a, b) { return rate(S.channels[b]) - rate(S.channels[a]); })[0];
      var wr = rate(S.channels[worst]);
      if (wr - med >= 8) {
        // modelled impact: if this channel only performed at the median of the others
        var total = S.n, fixedNeg = 0;
        Object.keys(S.channels).forEach(function (k) {
          fixedNeg += (k === worst) ? S.channels[k].n * med / 100 : S.channels[k].neg;
        });
        var delta = S.mix.negative - (fixedNeg / total * 100);
        out.push({
          priority: wr >= 55 ? "CRITICAL" : "HIGH",
          title: "Fix the " + worst + " first",
          diagnosis: "The " + worst + " runs at " + pct(wr) + "% negative against a " + pct(med) + "% median across other channels. This is a service failure, not a messaging problem.",
          evidence: S.channels[worst].neg + " of " + S.channels[worst].n + " " + worst + " reviews are negative; the other channels sit near " + pct(med) + "%.",
          action: "Freeze new features for two sprints and fix the failure path customers hit most. Measure weekly until the channel is within five points of the median.",
          impact: "Modelled: overall negativity falls from " + S.mix.negative + "% to " + pct(S.mix.negative - delta) + "% (-" + pct(delta) + " pts) if this channel only matched the median.",
          owner: OWNER[0][1],
          confidence: confidence(S.channels[worst].n, wr - med)
        });
      }
    }

    if (segs.length >= 2) {
      var hot = segs.filter(function (k) { return rate(S.segments[k]) >= 60; })
                    .sort(function (a, b) { return rate(S.segments[b]) - rate(S.segments[a]); });
      if (hot.length) {
        var names = hot.slice(0, 2);
        out.push({
          priority: "HIGH",
          title: "Protect " + names.join(" and "),
          diagnosis: "Your highest-value segments carry the most negativity. These are the customers with the longest remaining fee life, so the cost of losing them is not one transaction.",
          evidence: names.map(function (k) { return k + " " + pct(rate(S.segments[k])) + "% negative (" + S.segments[k].n + " reviews)"; }).join("; ") + ".",
          action: "Run a two-week listening sprint with these cohorts: call twenty of them, find the shared failure, fix it, then tell them what you fixed.",
          impact: "Retention work on " + names.length + " segments, not blanket campaigns on all five.",
          owner: "Customer Experience",
          confidence: confidence(S.segments[names[0]].n, rate(S.segments[names[0]]) - median(segs.map(function (k) { return rate(S.segments[k]); })))
        });
      }
      var cold = segs.filter(function (k) { return rate(S.segments[k]) <= 30 && S.segments[k].n <= 10; })
                     .sort(function (a, b) { return S.segments[a].n - S.segments[b].n; })[0];
      if (cold) {
        out.push({
          priority: "MEDIUM",
          title: "Low complaints are not satisfaction: " + cold,
          diagnosis: cold + " shows only " + pct(rate(S.segments[cold])) + "% negative, but on " + S.segments[cold].n + " reviews. An unhappy business client tends to leave quietly rather than write a review.",
          evidence: S.segments[cold].n + " reviews total — too few to read silence as approval.",
          action: "Survey twenty " + cold + " clients before their next renewal. Ask what would make them switch.",
          impact: "Converts a blind spot into evidence for roughly the cost of twenty phone calls.",
          owner: "Relationship Banking",
          confidence: { level: "Low", why: "explicitly low-volume: this is a hypothesis to test" }
        });
      }
    }

    var days = Object.keys(S.days || {}).sort();
    if (days.length >= 4) {
      var half = Math.floor(days.length / 2);
      var earlier = days.slice(0, half), later = days.slice(half);
      function agg(list) { var n = 0, g = 0; list.forEach(function (d) { n += S.days[d].n; g += S.days[d].neg; }); return n ? g / n * 100 : 0; }
      var a1 = agg(earlier), a2 = agg(later), move = a2 - a1;
      if (Math.abs(move) >= 8) {
        out.push({
          priority: move > 0 ? "HIGH" : "MEDIUM",
          title: move > 0 ? "Regression detected in the later period" : "Something worked: hold it",
          diagnosis: move > 0
            ? "Negativity rose " + pct(move) + " points between the two halves of this period. Sentiment moved before churn did, which is the point of measuring it."
            : "Negativity fell " + pct(Math.abs(move)) + " points between the two halves. A fix landed; the risk now is losing it quietly.",
          evidence: "First half " + pct(a1) + "% negative, second half " + pct(a2) + "% (" + (move > 0 ? "+" : "") + pct(move) + " pts).",
          action: move > 0
            ? "Compare release notes and incident logs against the date the trend turned. The instrument shows when; your logs show what."
            : "Write down what changed, assign an owner, and add this metric to the monthly review so the gain is defended.",
          impact: move > 0 ? "Catches a regression while customers are still complaining rather than after they leave." : "Turns one good month into a repeatable practice.",
          owner: "Head of Operations",
          confidence: confidence(Math.min(agg(earlier), agg(later)), Math.abs(move))
        });
      }
    }

    if (S.topTerms && S.topTerms.length) {
      var routed = [], seen = {};
      S.topTerms.forEach(function (t) {
        for (var i = 0; i < OWNER.length; i++) {
          if (OWNER[i][0].test(t) && !seen[OWNER[i][1]]) { seen[OWNER[i][1]] = 1; routed.push({ term: t, owner: OWNER[i][1] }); break; }
        }
      });
      if (routed.length) {
        out.push({
          priority: "MEDIUM",
          title: "Route the language customers actually use",
          diagnosis: "The strongest negative terms point at specific owners, so complaints can be assigned instead of absorbed by a general inbox.",
          evidence: routed.map(function (r) { return '"' + r.term + '" \u2192 ' + r.owner; }).join("; ") + ".",
          action: "Send each theme to its owner with ten verbatim reviews attached. No summary, just the customer's own words.",
          impact: "Turns an aggregate score into five work items with names on them.",
          owner: "Service Desk",
          confidence: { level: "Medium", why: "term frequency over negative reviews only" }
        });
      }
    }

    var order = { CRITICAL: 0, HIGH: 1, MEDIUM: 2 };
    return out.sort(function (a, b) { return order[a.priority] - order[b.priority]; }).slice(0, 4);
  }

  root.CitiAdvisor = { summarise: summarise, advise: advise };
})(typeof globalThis !== "undefined" ? globalThis : this);
