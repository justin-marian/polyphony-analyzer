"use strict";

function renderSummary(result) {
  var el = document.getElementById("summary");
  if (!el) return;

  el.innerHTML =
    chip("Utterances", result.summary.utterances) +
    chip("Speakers", result.summary.speakers.join(", ")) +
    chip("Voices", result.summary.voices) +
    chipCol("Divergences", result.summary.divergences, "#dc2626") +
    chipCol("Convergences", result.summary.convergences, "#16a34a");
}

function topicDotHtml(voice, voiceIndex, visibleVoiceIndices) {
  var localLane = getLocalVoiceLane(voiceIndex, visibleVoiceIndices);
  var left = topicLaneOffset(localLane, visibleVoiceIndices.length);

  return (
    '<span class="topic-dot topic-dot-v' + (voiceIndex % VOICE_COLORS.length) + '" ' +
    'title="topic: ' + escAttr(voice.label) + '" ' +
    'style="left:' + left + '%"></span>'
  );
}

function replyBadgeHtml(event, lane) {
  var isDiv = event.kind === "divergence";
  var cls = isDiv ? "reply-rel-div" : "reply-rel-conv";
  var txt = isDiv ? "D" : "C";
  var left = 14 + lane * 25;

  return (
    '<button type="button" class="reply-rel ' + cls + '" ' +
    'style="left:' + left + 'px" ' +
    'title="#' + event.utterance_a + ' → #' + event.utterance_b + ' (' + escAttr(event.trigger_word || "") + ')" ' +
    'onclick="scrollToUtt(' + event.utterance_a + ', [' + event.utterance_a + ',' + event.utterance_b + '])">' +
      '<span class="reply-rel-kind">' + txt + '</span>' +
      '<span class="reply-rel-src">' + event.utterance_a + '</span>' +
    '</button>'
  );
}

function renderUtterances(result) {
  var tbody = document.getElementById("utterance-body");
  if (!tbody) return;

  var utterances = result.utterances || [];
  var voices = getVoices(result);
  var events = getEvents(result);
  var active = activeTopic();

  var voiceMaps = buildVoiceMaps(voices);
  var visibleVoiceIndices = getVisibleVoiceIndices(voices);
  var visibleEvents = getVisibleEvents(voices, events);
  var activeSet = getActiveUtteranceSet(voices, events);
  var eventByTarget = indexEventsByTarget(visibleEvents);

  var rows = active
    ? utterances.filter(function (u) { return activeSet.has(u.index); })
    : utterances;

  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-cell">No utterances found for selected topic.</td></tr>';
    return;
  }

  tbody.innerHTML = rows.map(function (u) {
    var rowEvents = eventByTarget[u.index] || [];
    var rowClass = "";

    if (rowEvents.some(function (e) { return e.kind === "divergence"; })) {
      rowClass = " row-divergence";
    } else if (rowEvents.some(function (e) { return e.kind === "convergence"; })) {
      rowClass = " row-convergence";
    }

    var topicDots = (voiceMaps.voicesByUtterance[u.index] || [])
      .map(function (item) {
        if (active && item.label !== active) return "";
        return topicDotHtml(voices[item.voiceIndex], item.voiceIndex, visibleVoiceIndices);
      })
      .join("");

    var replyBadges = rowEvents
      .map(function (event, i) { return replyBadgeHtml(event, i % 4); })
      .join("") || '<span class="reply-empty"></span>';

    return (
      '<tr id="utt-' + u.index + '" class="utt-row' + rowClass + '" data-visible-utt="' + u.index + '">' +
        '<td class="col-nr">' + u.index + '</td>' +
        '<td class="col-user col-speaker">' + esc(u.speaker) + '</td>' +
        '<td class="col-text">' + highlightVoiceTerms(u.text, voiceMaps.colorByVoice) + '</td>' +
        '<td class="col-topic" data-utt="' + u.index + '">' + topicDots + '</td>' +
        '<td class="col-reply" data-utt="' + u.index + '">' + replyBadges + '</td>' +
        '<td class="col-presentation" data-utt="' + u.index + '"></td>' +
      '</tr>'
    );
  }).join("");

  renderPolyphonicOverlay(result);
}
