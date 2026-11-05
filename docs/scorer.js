/* TextBlob-compatible sentiment scorer (browser + Node).
   Uses TextBlob's own en-sentiment lexicon with modifier and negation rules.
   Calibrated against TextBlob on bundled reviews; agreement is reported on the site. */
(function (root) {
  "use strict";
  var LEX = null;
  var CFG = { intensifier: 1.3, diminisher: 0.5, negation: -0.5, punctuation: 1.0, norm: "hits", mode: "sentence" };

  var INTENSIFIERS = ["very","really","extremely","incredibly","absolutely","totally","highly","so","too","completely","utterly"];
  var DIMINISHERS  = ["slightly","somewhat","barely","hardly","marginally","fairly","quite","rather","partly"];
  var NEGATORS     = ["not","no","never","none","cannot","can't","dont","don't","doesn't","didn't","isn't","wasn't","weren't","won't","wouldn't","shouldn't","couldn't","n't","without","nothing"];

  function load(lexicon) { LEX = lexicon; }

  function tokens(text) {
    return String(text || "")
      .toLowerCase()
      .replace(/https?:\/\/\S+/g, " ")
      .replace(/[^a-z0-9'!.\s-]/g, " ")
      .split(/\s+/)
      .filter(Boolean);
  }

  function lookup(word) {
    if (!LEX) return 0;
    if (LEX[word] !== undefined) return LEX[word];
    var base = word.replace(/(ing|ed|es|s|ly)$/, "");
    if (LEX[base] !== undefined) return LEX[base];
    if (LEX[word + "s"] !== undefined) return LEX[word + "s"];
    return 0;
  }

  function analyse(text) {
    var toks = tokens(text);
    if (!toks.length) return { polarity: 0, subjectivity: 0, hits: 0, matched: [] };
    var scores = [], matched = [];
    for (var i = 0; i < toks.length; i++) {
      var w = toks[i].replace(/[!.]/g, "");
      var base = lookup(w);
      if (base !== 0) {
        var val = base, scale = 1;
        var prev = toks[i - 1] || "", prev2 = toks[i - 2] || "", prev3 = toks[i - 3] || "";
        if (INTENSIFIERS.indexOf(prev) >= 0) scale = CFG.intensifier;
        else if (DIMINISHERS.indexOf(prev) >= 0) scale = CFG.diminisher;
        else if (prev === "not" || prev === "no" || prev === "never") {
          scale = CFG.negation;
          if (INTENSIFIERS.indexOf(prev2) >= 0) scale *= CFG.intensifier;
        } else if (NEGATORS.indexOf(prev2) >= 0 || NEGATORS.indexOf(prev3) >= 0) {
          scale = CFG.negation;
        }
        val = val * scale;
        if (/!/.test(toks[i])) val *= CFG.punctuation;
        scores.push(val);
        matched.push({ word: w, value: Math.round(val * 100) / 100 });
      }
    }
    var sum = scores.reduce(function (a, b) { return a + b; }, 0);
    var den = scores.length;
    if (CFG.norm === "sqrt") den = Math.sqrt(scores.length);
    else if (CFG.norm === "tokens") den = toks.length;
    var pol = den ? sum / den : 0;
    pol = Math.max(-1, Math.min(1, pol));
    var subjective = scores.length / Math.max(toks.length, 1);
    return {
      polarity: Math.round(pol * 1000) / 1000,
      subjectivity: Math.round(subjective * 1000) / 1000,
      hits: scores.length,
      matched: matched.slice(0, 8)
    };
  }

  function analyseSentences(text) {
    var parts = String(text || "").split(/[.!?;]+/).map(function (p) { return p.trim(); }).filter(Boolean);
    if (!parts.length) parts = [String(text || "")];
    var vals = [], hits = 0, matched = [];
    for (var i = 0; i < parts.length; i++) {
      var r = analyse(parts[i]);
      if (r.hits > 0) { vals.push(r.polarity); hits += r.hits; matched = matched.concat(r.matched); }
    }
    if (!vals.length) return { polarity: 0, subjectivity: 0, hits: 0, matched: [] };
    var mean = vals.reduce(function (a, b) { return a + b; }, 0) / vals.length;
    mean = Math.max(-1, Math.min(1, mean));
    return { polarity: Math.round(mean * 1000) / 1000, subjectivity: Math.round((hits / parts.length) * 100) / 100,
             hits: hits, matched: matched.slice(0, 8), sentences: vals.length };
  }

  function label(p) { return p > 0.1 ? "Positive" : (p < -0.1 ? "Negative" : "Neutral"); }

    function score(text) { return CFG.mode === "sentence" ? analyseSentences(text) : analyse(text); }

  var api = { load: load, analyse: analyse, analyseSentences: analyseSentences, score: score, label: label, config: CFG };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.SentimentScorer = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
