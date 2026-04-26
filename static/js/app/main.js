"use strict";

document.addEventListener("DOMContentLoaded", function () {
  var sessionSelect = document.getElementById("session-select");
  var analyzeBtn = document.getElementById("analyze-btn");

  if (sessionSelect) {
    sessionSelect.addEventListener("change", handleSessionChange);
  }

  if (analyzeBtn) {
    analyzeBtn.addEventListener("click", handleAnalyzeClick);
  }

  loadSessions();
});