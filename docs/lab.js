/* "Analyse your own data" — paste text or upload a CSV, scored in the browser. */
(function () {
  "use strict";
  var S = window.SentimentScorer, parity = null, rows = [];

  fetch("parity.json").then(function (r) { return r.json(); }).then(function (p) { parity = p; renderParity(); }).catch(function () {});
  fetch("lexicon.json").then(function (r) { return r.json(); }).then(function (l) { S.load(l); })
    .catch(function () { msg("Lexicon failed to load.", true); });

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

  function findCol(header, names) {
    for (var i = 0; i < header.length; i++) {
      var h = header[i].toLowerCase().replace(/[^a-z]/g, "");
      for (var j = 0; j < names.length; j++) if (h.indexOf(names[j]) >= 0) return i;
    }
    return -1;
  }

  function fromCSV(text) {
    var table = parseCSV(text);
    if (!table.length) return [];
    var header = table[0], body = table.slice(1);
    var tIdx = findCol(header, ["reviewtext", "text", "review", "comment", "message", "feedback"]);
    if (tIdx < 0) { tIdx = header.length - 1; body = table; }
    var cIdx = findCol(header, ["channel", "source", "platform"]);
    var sIdx = findCol(header, ["segment", "customertype", "type"]);
    var dIdx = findCol(header, ["date", "time"]);
    var iIdx = findCol(header, ["reviewid", "id"]);
    return body.map(function (r) {
      return {
        id: iIdx >= 0 ? r[iIdx] : "", date: dIdx >= 0 ? r[dIdx] : "",
        channel: cIdx >= 0 ? r[cIdx] : "", segment: sIdx >= 0 ? r[sIdx] : "",
        text: (r[tIdx] || "").trim()
      };
    }).filter(function (r) { return r.text.length > 1; });
  }

  function render(scored, source) {
    rows = scored;
    var neg = scored.filter(function (r) { return r.sentiment === "Negative"; }).length;
    var pos = scored.filter(function (r) { return r.sentiment === "Positive"; }).length;
    var avg = scored.reduce(function (a, r) { return a + r.polarity; }, 0) / (scored.length || 1);
    var el = document.getElementById("labResults");
    if (!el) return;
    el.innerHTML =
      '<div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">' +
        tile("REVIEWS", scored.length, source) +
        tile("NEGATIVE", (100 * neg / scored.length).toFixed(1) + "%", neg + " reviews") +
        tile("POSITIVE", (100 * pos / scored.length).toFixed(1) + "%", pos + " reviews") +
        tile("AVG POLARITY", (avg >= 0 ? "+" : "") + avg.toFixed(3), "range -1 to +1") +
      '</div>' +
      '<div class="mt-4 max-h-72 overflow-auto rounded border border-slate-800">' +
        '<table class="w-full text-left text-[11px]"><thead class="bg-slate-900/70 text-slate-400 sticky top-0">' +
        '<tr><th class="px-3 py-2">Review</th><th class="px-3 py-2">Channel</th>' +
        '<th class="px-3 py-2 text-right">Polarity</th><th class="px-3 py-2">Sentiment</th></tr></thead><tbody>' +
        scored.map(function (r) {
          var col = r.sentiment === "Positive" ? "text-emerald-400" : r.sentiment === "Negative" ? "text-red-400" : "text-amber-300";
          return '<tr class="border-t border-slate-800/70"><td class="px-3 py-2 text-slate-300">' + esc(r.text.slice(0, 110)) +
            '</td><td class="px-3 py-2 text-slate-500">' + esc(r.channel || "—") +
            '</td><td class="px-3 py-2 text-right font-mono ' + col + '">' + r.polarity.toFixed(3) +
            '</td><td class="px-3 py-2 ' + col + '">' + r.sentiment + '</td></tr>';
        }).join("") +
      '</tbody></table></div>' +
      '<button id="labDownload" class="mt-3 rounded bg-cyan-500/20 border border-cyan-400/40 px-3 py-1.5 text-[11px] font-bold text-cyan-200 hover:bg-cyan-500/30">Download scored CSV</button>';
    document.getElementById("labDownload").onclick = download;
  }

  function tile(label, value, sub) {
    return '<div class="rounded-lg border border-slate-800 bg-slate-900/50 p-3">' +
      '<div class="text-[10px] tracking-widest text-slate-500">' + label + '</div>' +
      '<div class="mt-1 text-xl font-bold text-white">' + value + '</div>' +
      '<div class="text-[10px] text-slate-500">' + esc(sub) + '</div></div>';
  }

  function download() {
    var head = "Review_ID,Date,Channel,Customer_Segment,Review_Text,Polarity,Subjectivity,Sentiment\n";
    var body = rows.map(function (r) {
      return [r.id, r.date, r.channel, r.segment, '"' + String(r.text).replace(/"/g, '""') + '"',
              r.polarity, r.subjectivity, r.sentiment].join(",");
    }).join("\n");
    var blob = new Blob([head + body], { type: "text/csv" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = "scored_reviews.csv"; a.click();
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
      msg("Scored " + lines.length + " pasted lines with the browser engine.");
    };

    if (file) file.onchange = function (e) {
      var f = e.target.files && e.target.files[0];
      if (!f) return;
      var reader = new FileReader();
      reader.onload = function () {
        var recs = fromCSV(String(reader.result));
        if (!recs.length) { msg("No reviews found in that file. Need a column named Review_Text, Text or Review.", true); return; }
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
