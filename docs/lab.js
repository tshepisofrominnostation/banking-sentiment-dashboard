/* "Analyse your own data" — paste text or upload a CSV, scored in the browser. */
(function () {
  "use strict";
  var S = window.SentimentScorer, parity = null, rows = [];

  fetch("parity.json").then(function (r) { return r.json(); }).then(function (p) { parity = p; renderParity(); }).catch(function () {});
  // base TextBlob lexicon + documented banking supplement
  Promise.all([
    fetch("lexicon.json").then(function (r) { return r.json(); }),
    fetch("domain.json").then(function (r) { return r.json(); }).catch(function () { return { terms: {} }; })
  ]).then(function (res) {
    var lex = res[0], extra = (res[1] && res[1].terms) || {}, k;
    for (k in extra) if (Object.prototype.hasOwnProperty.call(extra, k)) lex[k] = extra[k];
    S.load(lex);
    window.__lexiconLoaded = true;
  }).catch(function () { msg("Lexicon failed to load.", true); });

  function msg(t, err) {
    var m = document.getElementById("labMsg");
    if (!m) return;
    m.textContent = t;
    m.className = err ? "text-[11px] text-red-400 mt-2" : "text-[11px] text-slate-400 mt-2";
  }

  function renderParity() {
    var el = document.getElementById("labParity");
    if (!el || !parity) return;
    el.innerHTML = "Browser engine matches the Python TextBlob label on <b class='text-cyan-300'>" +
      parity.label_matches + " of " + parity.reviews + " reviews (" +
      (parity.label_agreement * 100).toFixed(1) + "%)</b> · mean polarity error " + parity.mean_abs_error;
  }

  function parseCSV(text) {
    var out = [], row = [], cur = "", q = false, i, c;
    for (i = 0; i < text.length; i++) {
      c = text[i];
      if (q) {
        if (c === '"' && text[i + 1] === '"') { cur += '"'; i++; }
        else if (c === '"') q = false;
        else cur += c;
      } else if (c === '"') q = true;
      else if (c === ",") { row.push(cur); cur = ""; }
      else if (c === "\n" || c === "\r") { if (cur !== "" || row.length) { row.push(cur); out.push(row); } row = []; cur = ""; }
      else cur += c;
    }
    if (cur !== "" || row.length) { row.push(cur); out.push(row); }
    return out.filter(function (r) { return r.length && r.join("").trim() !== ""; });
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function scoreRecords(list) {
    return list.map(function (r, i) {
      var s = S.score(r.text);
      return {
        id: r.id || ("ROW-" + (i + 1)), date: r.date || "", channel: r.channel || "",
        segment: r.segment || "", text: r.text,
        polarity: s.polarity, subjectivity: s.subjectivity, sentiment: S.label(s.polarity)
      };
    });
  }

  function findCol(header, names, exclude) {
    var norm = header.map(function (h) { return h.toLowerCase().replace(/[^a-z]/g, ""); });
    var i, j, blocked;
    // pass 1: exact name match (handles Channel vs Customer_Segment cleanly)
    for (j = 0; j < names.length; j++) {
      i = norm.indexOf(names[j]);
      if (i >= 0) return i;
    }
    // pass 2: substring match, skipping obvious id/date columns
    for (j = 0; j < names.length; j++) {
      for (i = 0; i < norm.length; i++) {
        blocked = false;
        for (var k = 0; k < (exclude || []).length; k++) if (norm[i].indexOf(exclude[k]) >= 0) blocked = true;
        if (!blocked && norm[i].indexOf(names[j]) >= 0) return i;
      }
    }
    return -1;
  }

  function fromCSV(text) {
    var table = parseCSV(text);
    if (!table.length) return [];
    var header = table[0], body = table.slice(1);
    var tIdx = findCol(header, ["reviewtext", "text", "comment", "message", "feedback", "review"], ["id"]);
    if (tIdx < 0) { tIdx = header.length - 1; body = table; }
    var cIdx = findCol(header, ["channel", "source", "platform"], ["id"]);
    var sIdx = findCol(header, ["customersegment", "segment", "customertype", "type"], ["id"]);
    var dIdx = findCol(header, ["date", "time"], ["id"]);
    var iIdx = findCol(header, ["reviewid", "id"]);
    return body.map(function (r) {
      return {
        id: iIdx >= 0 ? r[iIdx] : "", date: dIdx >= 0 ? r[dIdx] : "",
        channel: cIdx >= 0 ? r[cIdx] : "", segment: sIdx >= 0 ? r[sIdx] : "",
        text: (r[tIdx] || "").trim()
      };
    }).filter(function (r) { return r.text.length > 1; });
  }

  function tile(label, value, sub) {
    return '<div class="rounded-lg border px-3 py-2" style="border-color:var(--line);background:var(--panel2)">' +
      '<div class="text-[10px] tracking-widest" style="color:var(--mut)">' + label + '</div>' +
      '<div class="mt-1 text-xl font-bold" style="color:var(--ink)">' + value + '</div>' +
      '<div class="text-[10px]" style="color:var(--mut);opacity:.8">' + esc(sub) + '</div></div>';
  }

  function adviseUploaded(records) {
    if (!window.CitiAdvisorUI) return;
    window.CitiAdvisorUI.render(records);
  }

  function render(scored, source) {
    rows = scored;
    var n = scored.length || 1;
    var neg = scored.filter(function (r) { return r.sentiment === "Negative"; }).length;
    var pos = scored.filter(function (r) { return r.sentiment === "Positive"; }).length;
    var avg = scored.reduce(function (a, r) { return a + r.polarity; }, 0) / n;
    var el = document.getElementById("labResults");
    if (!el) return;
    el.innerHTML =
      '<div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">' +
        tile("REVIEWS", scored.length, source) +
        tile("NEGATIVE", (100 * neg / n).toFixed(1) + "%", neg + " reviews") +
        tile("POSITIVE", (100 * pos / n).toFixed(1) + "%", pos + " reviews") +
        tile("AVG POLARITY", (avg >= 0 ? "+" : "") + avg.toFixed(3), "range -1 to +1") +
      '</div>' +
      '<div class="mt-4 max-h-72 overflow-auto rounded" style="border:1px solid var(--line)">' +
        '<table class="w-full text-left text-[11px]"><thead style="background:var(--panel2);color:var(--mut);position:sticky;top:0">' +
        '<tr><th class="px-3 py-2">Review</th><th class="px-3 py-2">Channel</th>' +
        '<th class="px-3 py-2 text-right">Polarity</th><th class="px-3 py-2">Sentiment</th></tr></thead><tbody>' +
        scored.map(function (r) {
          var c = r.sentiment === "Negative" ? "var(--red)" : (r.sentiment === "Positive" ? "var(--green)" : "var(--amber)");
          return '<tr style="border-top:1px solid var(--line)">' +
            '<td class="px-3 py-1" style="color:var(--ink);opacity:.9">' + esc(String(r.text).slice(0, 110)) + '</td>' +
            '<td class="px-3 py-1" style="color:var(--mut)">' + esc(r.channel || "—") + '</td>' +
            '<td class="px-3 py-1 text-right" style="font-variant-numeric:tabular-nums">' + r.polarity.toFixed(3) + '</td>' +
            '<td class="px-3 py-1" style="color:' + c + '">' + esc(r.sentiment) + '</td></tr>';
        }).join("") +
        '</tbody></table></div>' +
      '<div class="mt-3"><button class="btn2" id="labDownload">Download scored CSV</button></div>';
    var dl = document.getElementById("labDownload");
    if (dl) dl.onclick = download;
    adviseUploaded(scored.map(function (r) {
      return { text: r.text, sentiment: r.sentiment, channel: r.channel, segment: r.segment, date: r.date };
    }));
  }

  function download() {
    var head = "Review_ID,Date,Channel,Customer_Segment,Review_Text,Polarity,Subjectivity,Sentiment\n";
    var body = rows.map(function (r) {
      return [r.id, r.date, r.channel, r.segment, '"' + String(r.text).replace(/"/g, '""') + '"',
              r.polarity, r.subjectivity, r.sentiment].join(",");
    }).join("\n");
    var blob = new Blob([head + body], { type: "text/csv" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = "citi_analysis_scored.csv"; a.click();
  }

  function wire() {
    var ta = document.getElementById("labText");
    var file = document.getElementById("labFile");
    var sample = document.getElementById("labSample");
    var paste = document.getElementById("labPaste");

    if (paste) paste.onclick = function () {
      var lines = (ta.value || "").split("\n").map(function (l) { return l.trim(); }).filter(function (l) { return l.length > 2; });
      if (!lines.length) { msg("Paste one review per line first.", true); return; }
      render(scoreRecords(lines.map(function (l) { return { text: l }; })), "pasted text");
      msg("Scored " + lines.length + " pasted lines in your browser.");
    };

    if (file) file.onchange = function (e) {
      var f = e.target.files && e.target.files[0];
      if (!f) return;
      var reader = new FileReader();
      reader.onload = function () {
        var recs = fromCSV(String(reader.result));
        if (!recs.length) { msg("No reviews found. Need a column named Review_Text, Text or Review.", true); return; }
        render(scoreRecords(recs), f.name);
        msg("Scored " + recs.length + " rows from " + f.name + " — nothing was uploaded, it ran in your browser.");
      };
      reader.readAsText(f);
    };

    if (sample) sample.onclick = function () {
      fetch("sample_upload.csv").then(function (r) { return r.text(); }).then(function (t) {
        var recs = fromCSV(t);
        render(scoreRecords(recs), "sample_upload.csv");
        msg("Loaded the bundled sample: " + recs.length + " tricky reviews (sarcasm, negation, local terms).");
      }).catch(function () { msg("Could not load the sample file.", true); });
    };
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", wire);
  else wire();
})();
