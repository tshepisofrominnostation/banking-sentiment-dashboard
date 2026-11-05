/* Renders Citi Advisor cards from the currently selected dataset. */
(function () {
  "use strict";
  var PRIO = { CRITICAL: "var(--red)", HIGH: "var(--amber)", MEDIUM: "var(--green)" };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function card(a, idx) {
    var col = PRIO[a.priority] || "var(--mut)";
    return '<article class="rounded-lg border p-4" style="border-color:var(--line);background:var(--panel2)">'
      + '<div class="flex items-baseline gap-3 flex-wrap">'
      + '<span class="text-[10px] font-bold px-2 py-0.5 rounded" style="background:' + col + '22;color:' + col + ';border:1px solid ' + col + '55">' + esc(a.priority) + '</span>'
      + '<h3 class="font-bold" style="color:var(--ink)">' + esc(a.title) + '</h3>'
      + '<span class="text-[11px] ml-auto" style="color:var(--mut)">owner: ' + esc(a.owner) + ' &middot; confidence: ' + esc(a.confidence.level) + '</span>'
      + '</div>'
      + '<p class="text-[13px] mt-2" style="color:var(--ink);opacity:.92">' + esc(a.diagnosis) + '</p>'
      + '<p class="text-[12px] mt-2" style="color:var(--mut)"><b style="color:var(--amber)">Evidence.</b> ' + esc(a.evidence) + '</p>'
      + '<p class="text-[12px] mt-1" style="color:var(--mut)"><b style="color:var(--green)">Do this.</b> ' + esc(a.action) + '</p>'
      + '<p class="text-[12px] mt-1" style="color:var(--mut)"><b style="color:var(--cyan)">Impact.</b> ' + esc(a.impact) + '</p>'
      + '<p class="text-[11px] mt-2" style="color:var(--mut);opacity:.75">why ' + esc(a.confidence.level.toLowerCase()) + ' confidence: ' + esc(a.confidence.why) + '</p>'
      + '</article>';
  }

  function render(rows) {
    var box = document.getElementById("advisorList");
    if (!box || !window.CitiAdvisor) return;
    var advice = window.CitiAdvisor.advise(window.CitiAdvisor.summarise(rows));
    if (!advice.length) {
      box.innerHTML = '<p class="text-[12px]" style="color:var(--mut)">Not enough data for a confident recommendation yet. Load at least twenty reviews with a channel or segment column.</p>';
      return;
    }
    box.innerHTML = advice.map(card).join("");
  }

  window.CitiAdvisorUI = { render: render };

  // hook the dataset the dashboard already renders
  var tries = 0;
  var timer = setInterval(function () {
    tries++;
    var data = window.__citiData || null;
    if (data && data.reviews) { clearInterval(timer); render(data.reviews); }
    else if (tries > 40) { clearInterval(timer); }
  }, 250);
})();
