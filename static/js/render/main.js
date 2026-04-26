"use strict";

function highlightRows(indices) {
  document.querySelectorAll("tr.highlight-row").forEach(function (row) {
    row.classList.remove("highlight-row");
  });

  indices.forEach(function (idx) {
    var row = document.getElementById("utt-" + idx);
    if (row) row.classList.add("highlight-row");
  });
}

function scrollToUtt(index, alsoHighlight) {
  highlightRows(alsoHighlight || [index]);

  var row = document.getElementById("utt-" + index);
  if (row) row.scrollIntoView({ behavior: "smooth", block: "center" });
}

function renderArcOverlay() {
  if (window.lastAnalysisResult) renderPolyphonicOverlay(window.lastAnalysisResult);
}

function renderAll(result) {
  window.lastAnalysisResult = result;

  renderSummary(result);
  renderTopicFilter(result);
  renderUtterances(result);
  renderVoices(result);
  renderEvents(result);
  renderSpeakerStats(result);
  renderDynamic(result);

  setTimeout(function () {
    renderPolyphonicOverlay(result);
  }, 0);

  if (window.lucide) lucide.createIcons();
}
