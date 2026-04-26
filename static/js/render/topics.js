"use strict";

function buildVoiceMaps(voices) {
  var colorByVoice = {};
  var voicesByUtterance = {};

  voices.forEach(function (voice, voiceIndex) {
    var label = topicKey(voice.label);
    colorByVoice[label] = voiceIndex % VOICE_COLORS.length;

    (voice.utterance_indices || []).forEach(function (uttIndex) {
      if (!voicesByUtterance[uttIndex]) voicesByUtterance[uttIndex] = [];
      voicesByUtterance[uttIndex].push({ label: label, voiceIndex: voiceIndex });
    });
  });

  return { colorByVoice: colorByVoice, voicesByUtterance: voicesByUtterance };
}

function getVisibleVoiceIndices(voices) {
  var active = activeTopic();
  return voices
    .map(function (_, index) { return index; })
    .filter(function (index) { return !active || topicKey(voices[index].label) === active; });
}

function getLocalVoiceLane(voiceIndex, visibleVoiceIndices) {
  var lane = visibleVoiceIndices.indexOf(voiceIndex);
  return lane >= 0 ? lane : 0;
}

function topicLaneOffset(localLane, totalLanes) {
  if (totalLanes <= 1) return 50;
  var min = 30;
  var max = 70;
  return min + ((max - min) * localLane) / (totalLanes - 1);
}

function topicDotCenterX(cell, voiceIndex, voices, visibleVoiceIndices) {
  var localLane = getLocalVoiceLane(voiceIndex, visibleVoiceIndices);
  var percent = topicLaneOffset(localLane, visibleVoiceIndices.length);
  return cell.left + (cell.width * percent) / 100;
}

function replyLaneX(cell, lane) {
  return cell.left + 26 + lane * 25;
}

function utteranceHasTopic(utteranceIndex, topicLabel, voices) {
  var wanted = topicKey(topicLabel);
  return voices.some(function (voice) {
    return topicKey(voice.label) === wanted &&
      (voice.utterance_indices || []).indexOf(utteranceIndex) !== -1;
  });
}

function getActiveUtteranceSet(voices, events) {
  var active = activeTopic();
  var activeSet = new Set();

  if (!active) return activeSet;

  voices.forEach(function (voice) {
    if (topicKey(voice.label) !== active) return;
    (voice.utterance_indices || []).forEach(function (idx) { activeSet.add(idx); });
  });

  events.forEach(function (event) {
    var eventVoices = (event.voices_involved || []).map(topicKey);
    if (
      eventVoices.indexOf(active) !== -1 ||
      utteranceHasTopic(event.utterance_a, active, voices) ||
      utteranceHasTopic(event.utterance_b, active, voices)
    ) {
      activeSet.add(event.utterance_a);
      activeSet.add(event.utterance_b);
    }
  });

  return activeSet;
}

function getVisibleEvents(voices, events) {
  var active = activeTopic();
  if (!active) return events;

  return events.filter(function (event) {
    var eventVoices = (event.voices_involved || []).map(topicKey);
    return eventVoices.indexOf(active) !== -1 ||
      utteranceHasTopic(event.utterance_a, active, voices) ||
      utteranceHasTopic(event.utterance_b, active, voices);
  });
}

function indexEventsByTarget(events) {
  var grouped = {};
  events.forEach(function (event) {
    if (!grouped[event.utterance_b]) grouped[event.utterance_b] = [];
    grouped[event.utterance_b].push(event);
  });
  return grouped;
}

function setTopicFilter(label) {
  ACTIVE_TOPIC_LABEL = label ? topicKey(label) : null;
  if (window.lastAnalysisResult) renderAll(window.lastAnalysisResult);
}

function highlightVoiceTerms(text, colorByVoice) {
  var html = esc(text);

  Object.keys(colorByVoice)
    .sort(function (a, b) { return b.length - a.length; })
    .forEach(function (label) {
      var colorIndex = colorByVoice[label];
      var re = new RegExp("\\b(" + escRe(label) + ")\\b", "gi");
      html = html.replace(re, '<mark class="voice v' + colorIndex + '">$1</mark>');
    });

  return html;
}

function renderTopicFilter(result) {
  var host = document.getElementById("topic-filter-bar");

  if (!host) {
    var summary = document.getElementById("summary");
    if (!summary || !summary.parentNode) return;

    host = document.createElement("div");
    host.id = "topic-filter-bar";
    host.className = "topic-filter-bar";
    summary.parentNode.insertBefore(host, summary.nextSibling);
  }

  var voices = getVoices(result);

  var topics = voices.map(function (voice, i) {
    return (
      '<span class="topic-pill">' +
        '<span class="topic-filter-swatch" style="background:' + VOICE_COLORS[i % VOICE_COLORS.length] + '"></span>' +
        esc(voice.label) +
      '</span>'
    );
  }).join("");

  host.innerHTML =
    '<span class="topic-filter-label">Topics:</span>' +
    topics;
}
