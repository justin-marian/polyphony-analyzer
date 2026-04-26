"use strict";

function normalizeResult(data, fallbackName) {
  var events = data.inter_animation_events || data.events || [];

  return {
    name: data.name || data.chat_log_name || fallbackName,
    utterances: data.utterances || [],
    voices: data.voices || [],
    inter_animation_events: events,
    events: events,
    speaker_stats: data.speaker_stats || {},
    summary: {
      utterances: data.summary?.utterances ?? (data.utterances || []).length,
      speakers: data.summary?.speakers ?? [],
      voices: data.summary?.voices ?? (data.voices || []).length,
      divergences: data.summary?.divergences ?? events.filter(e => e.kind === "divergence").length,
      convergences: data.summary?.convergences ?? events.filter(e => e.kind === "convergence").length
    }
  };
}

function finishAnalysis(result) {
  renderAll(result);

  setStatus(
    "Done \u2014 " +
    result.summary.utterances + " utterances, " +
    result.summary.voices + " voices, " +
    result.summary.divergences + " divergences, " +
    result.summary.convergences + " convergences."
  );

  var analyzeBtn = document.getElementById("analyze-btn");
  if (analyzeBtn) analyzeBtn.disabled = false;
}

function handleAnalyzeClick() {
  var chatInput = document.getElementById("chat-input");
  var sessionSelect = document.getElementById("session-select");
  var analyzeBtn = document.getElementById("analyze-btn");

  if (!chatInput || !analyzeBtn) return;

  var text = chatInput.value.trim();

  if (!text) {
    setStatus("Paste a chat log or pick a sample first.", true);
    return;
  }

  analyzeBtn.disabled = true;
  setStatus("Analyzing with Python engine\u2026");

  var selectedOption = sessionSelect
    ? sessionSelect.options[sessionSelect.selectedIndex]
    : null;

  var name = selectedOption && selectedOption.value
    ? selectedOption.text
    : "Pasted Chat";

  analyzeOnServer(text, name)
    .then(function (data) {
      finishAnalysis(normalizeResult(data, name));
    })
    .catch(function (err) {
      setStatus(
        err.message || "Analysis failed. Make sure the Python server is running.",
        true
      );

      analyzeBtn.disabled = false;
    });
}
