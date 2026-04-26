"use strict";

function renderVoices(result) {
  var host = document.getElementById("voices-list");
  if (!host) return;

  var voices = getVoices(result);

  if (!voices.length) {
    host.innerHTML = '<p class="empty-cell">No voices detected.</p>';
    return;
  }

  host.innerHTML = voices.map(function (voice, i) {
    return (
      '<div class="voice-item">' +
        '<span class="vi-swatch" style="background:' + VOICE_COLORS[i % VOICE_COLORS.length] + '"></span>' +
        '<div class="vi-body">' +
          '<div class="label">' + esc(voice.label) + '</div>' +
          '<div class="meta">freq ' + esc(voice.frequency) + ' · ' + esc((voice.speakers || []).join(", ")) + '</div>' +
        '</div>' +
      '</div>'
    );
  }).join("");
}

function eventHtml(event) {
  var voices = event.voices_involved && event.voices_involved.length
    ? '<span class="trigger-voices">voices: ' + esc(event.voices_involved.join(", ")) + '</span>'
    : "";

  return (
    '<li class="' + esc(event.kind) + '" onclick="scrollToUtt(' + event.utterance_b + ', [' + event.utterance_a + ',' + event.utterance_b + '])">' +
      '<span class="ev-pair">No. ' + event.utterance_a + ' to No. ' + event.utterance_b + '</span>' +
      '<span><strong>' + esc(event.speaker_a) + '</strong> with <strong>' + esc(event.speaker_b) + '</strong></span>' +
      '<span class="trigger">trigger: “' + esc(event.trigger_word || event.trigger || "") + '”</span>' +
      voices +
    '</li>'
  );
}

function renderEvents(result) {
  var events = getEvents(result);
  var divs = events.filter(function (e) { return e.kind === "divergence"; });
  var convs = events.filter(function (e) { return e.kind === "convergence"; });

  var divCount = document.getElementById("div-count");
  var convCount = document.getElementById("conv-count");

  if (divCount) divCount.textContent =
    result.summary && result.summary.divergences !== undefined
      ? result.summary.divergences
      : divs.length;

  if (convCount) convCount.textContent =
    result.summary && result.summary.convergences !== undefined
      ? result.summary.convergences
      : convs.length;

  var divList = document.getElementById("div-list");
  var convList = document.getElementById("conv-list");

  if (divList) divList.innerHTML =
    divs.map(eventHtml).join("") || '<li class="empty-cell">None detected.</li>';

  if (convList) convList.innerHTML =
    convs.map(eventHtml).join("") || '<li class="empty-cell">None detected.</li>';
}

function renderSpeakerStats(result) {
  var host = document.getElementById("speaker-stats");
  if (!host) return;

  var entries = Object.entries(result.speaker_stats || {});
  if (!entries.length) {
    host.innerHTML = '<p class="empty-cell">No speaker stats.</p>';
    return;
  }

  host.innerHTML = entries.map(function (entry) {
    var name = entry[0];
    var stats = entry[1];
    return (
      '<div class="speaker-row">' +
        '<div class="name">' + esc(name) + '</div>' +
        '<div class="nums">' +
          esc(stats.utterance_count) + ' utterances · avg ' + Number(stats.avg_length || 0).toFixed(1) + ' tokens<br>' +
          '<span class="div-label">' + esc(stats.divergences_initiated || 0) + ' div</span> / ' +
          '<span class="conv-label">' + esc(stats.convergences_initiated || 0) + ' conv</span>' +
        '</div>' +
      '</div>'
    );
  }).join("");
}

function renderDynamic(result) {
  var host = document.getElementById("dynamic-panel");
  if (!host) return;

  var events = getEvents(result);

  var divs = result.summary && result.summary.divergences !== undefined
    ? result.summary.divergences
    : events.filter(function (e) { return e.kind === "divergence"; }).length;

  var convs = result.summary && result.summary.convergences !== undefined
    ? result.summary.convergences
    : events.filter(function (e) { return e.kind === "convergence"; }).length;
  var total = divs + convs;
  var divPct = total ? Math.round(divs / total * 100) : 0;
  var convPct = total ? Math.round(convs / total * 100) : 0;

  var label = "BALANCED";
  var cls = "dynamic-balanced";
  if (divs > convs) {
    label = "Predominantly DIVERGENT";
    cls = "dynamic-div";
  } else if (convs > divs) {
    label = "Predominantly CONVERGENT";
    cls = "dynamic-conv";
  }

  host.innerHTML =
    '<div class="dynamic-label ' + cls + '">' + label + '</div>' +
    '<div class="dynamic-bar-wrap">' +
      '<div class="dynamic-bar-div" style="width:' + divPct + '%"></div>' +
      '<div class="dynamic-bar-conv" style="width:' + convPct + '%"></div>' +
    '</div>' +
    '<div class="dynamic-legend">' +
      '<span class="dleg-conv">&#8613; convergence: ' + convs + ' (' + convPct + '%)</span>' +
      '<span class="dleg-div">&#8615; divergence: ' + divs + ' (' + divPct + '%)</span>' +
    '</div>';
}
