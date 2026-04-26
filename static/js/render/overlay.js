"use strict";

function createOverlaySvg(table, tableRect, scrollRect, scroll) {
  var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");

  svg.setAttribute("id", "polyphonic-overlay-svg");
  svg.setAttribute("class", "polyphonic-overlay-svg");
  svg.setAttribute("width", table.offsetWidth);
  svg.setAttribute("height", table.offsetHeight);
  svg.setAttribute("viewBox", "0 0 " + table.offsetWidth + " " + table.offsetHeight);
  svg.style.left = (tableRect.left - scrollRect.left + scroll.scrollLeft) + "px";
  svg.style.top = (tableRect.top - scrollRect.top + scroll.scrollTop) + "px";

  svg.innerHTML =
    '<defs>' +
      '<marker id="arr-red-small" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">' +
        '<polygon points="0 0, 7 3.5, 0 7" fill="#dc2626"></polygon>' +
      '</marker>' +
      '<marker id="arr-green-small" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">' +
        '<polygon points="0 0, 7 3.5, 0 7" fill="#16a34a"></polygon>' +
      '</marker>' +
      '<marker id="arr-black-small" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">' +
        '<polygon points="0 0, 6 3, 0 6" fill="#111827"></polygon>' +
      '</marker>' +
    '</defs>';

  return svg;
}

function cellBox(table, tableRect, selector, index) {
  var cell = table.querySelector(selector + '[data-utt="' + index + '"]');
  if (!cell) return null;

  var rect = cell.getBoundingClientRect();
  return {
    x: rect.left - tableRect.left + rect.width / 2,
    y: rect.top - tableRect.top + rect.height / 2,
    left: rect.left - tableRect.left,
    right: rect.right - tableRect.left,
    top: rect.top - tableRect.top,
    bottom: rect.bottom - tableRect.top,
    width: rect.width,
    height: rect.height
  };
}

function topicDotPoint(tableRect, utteranceIndex, voiceIndex) {
  var cell = document.querySelector('td.col-topic[data-utt="' + utteranceIndex + '"]');
  if (!cell) return null;

  var dot = cell.querySelector(".topic-dot-v" + (voiceIndex % VOICE_COLORS.length));
  if (!dot) return null;

  var rect = dot.getBoundingClientRect();

  return {
    x: rect.left - tableRect.left + rect.width / 2,
    y: rect.top - tableRect.top + rect.height / 2
  };
}

function appendPath(svg, d, color, width, marker, opacity, dash, cls) {
  var path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", d);
  path.setAttribute("fill", "none");
  path.setAttribute("stroke", color);
  path.setAttribute("stroke-width", width || 2);
  path.setAttribute("stroke-linecap", "round");
  path.setAttribute("stroke-linejoin", "round");
  if (marker) path.setAttribute("marker-end", "url(#" + marker + ")");
  if (opacity) path.setAttribute("opacity", opacity);
  if (dash) path.setAttribute("stroke-dasharray", dash);
  if (cls) path.setAttribute("class", cls);
  svg.appendChild(path);
  return path;
}

function appendCircle(svg, x, y, r, color, cls) {
  var circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  circle.setAttribute("cx", x);
  circle.setAttribute("cy", y);
  circle.setAttribute("r", r);
  circle.setAttribute("fill", color);
  if (cls) circle.setAttribute("class", cls);
  svg.appendChild(circle);
  return circle;
}

function appendText(svg, x, y, text, color) {
  var node = document.createElementNS("http://www.w3.org/2000/svg", "text");
  node.setAttribute("x", x);
  node.setAttribute("y", y);
  node.setAttribute("fill", color);
  node.setAttribute("font-size", "10");
  node.setAttribute("font-weight", "850");
  node.textContent = text;
  svg.appendChild(node);
  return node;
}

function drawTopicLines(svg, table, tableRect, voices, visibleVoiceIndices, active) {
  voices.forEach(function (voice, voiceIndex) {
    if (active && topicKey(voice.label) !== active) return;

    var color = VOICE_COLORS[voiceIndex % VOICE_COLORS.length];

    var points = (voice.utterance_indices || [])
      .slice()
      .sort(function (a, b) { return a - b; })
      .map(function (idx) {
        var row = document.getElementById("utt-" + idx);
        if (!row) return null; // important when topic filter is active

        var cell = cellBox(table, tableRect, "td.col-topic", idx);
        if (!cell) return null;

        return {
          x: topicDotCenterX(cell, voiceIndex, voices, visibleVoiceIndices),
          y: cell.y
        };
      })
      .filter(Boolean);

    points.forEach(function (point) {
      appendCircle(svg, point.x, point.y, 4.5, color, "topic-node");
    });

    for (var i = 0; i < points.length - 1; i++) {
      appendPath(
        svg,
        "M " + points[i].x + " " + points[i].y +
        " L " + points[i + 1].x + " " + points[i + 1].y,
        color,
        2,
        null,
        "0.62",
        null,
        "topic-line"
      );
    }
  });
}

function firstEventVoiceIndex(event, voices, active) {
  var labels = (event.voices_involved || []).map(topicKey);
  if (active) labels = labels.filter(function (label) { return label === active; });

  var target = labels[0];
  var idx = voices.findIndex(function (voice) { return topicKey(voice.label) === target; });
  return idx >= 0 ? idx : 0;
}

function drawTopicToReplyLinks(svg, table, tableRect, voices, visibleVoiceIndices, events, active) {
  events.forEach(function (event, i) {
    var voiceIndex = firstEventVoiceIndex(event, voices, active);
    var source = cellBox(table, tableRect, "td.col-topic", event.utterance_a);
    var target = cellBox(table, tableRect, "td.col-reply", event.utterance_b);
    if (!source || !target) return;

    var sx = topicDotCenterX(source, voiceIndex, voices, visibleVoiceIndices);
    var sy = source.y;
    var tx = replyLaneX(target, i % 4);
    var ty = target.y;
    var cx = (sx + tx) / 2;
    var color = VOICE_COLORS[voiceIndex % VOICE_COLORS.length];

    appendPath(svg, "M " + sx + " " + sy + " C " + cx + " " + sy + ", " + cx + " " + ty + ", " + tx + " " + ty,
      color, 1.3, null, "0.34", null, "topic-reply-link");
  });
}

function drawSmallReplyLinks(svg, table, tableRect, events) {
  events.forEach(function (event, i) {
    var source = cellBox(table, tableRect, "td.col-reply", event.utterance_a);
    var target = cellBox(table, tableRect, "td.col-reply", event.utterance_b);
    if (!source || !target) return;

    var lane = i % 4;
    var x = replyLaneX(source, lane);
    var y1 = source.y;
    var y2 = target.y;
    var bend = 12 + lane * 6;

    appendPath(svg, "M " + x + " " + y1 + " C " + (x + bend) + " " + y1 + ", " + (x + bend) + " " + y2 + ", " + x + " " + y2,
      "#111827", 1.15, "arr-black-small", "0.48", null, "reply-link-small");
  });
}

function drawPresentationLinks(svg, table, tableRect, presCells, events) {
  var first = presCells[0].getBoundingClientRect();
  var last = presCells[presCells.length - 1].getBoundingClientRect();
  var left = first.left - tableRect.left;
  var right = first.right - tableRect.left;
  var spineX = left + 32;
  var topY = first.top - tableRect.top + first.height / 2;
  var bottomY = last.bottom - tableRect.top - last.height / 2;

  appendPath(svg, "M " + spineX + " " + topY + " L " + spineX + " " + bottomY,
    "#9ca3af", 1.4, null, "0.42", "4,5", "presentation-spine");

  events.forEach(function (event, i) {
    var source = cellBox(table, tableRect, "td.col-presentation", event.utterance_a);
    var target = cellBox(table, tableRect, "td.col-presentation", event.utterance_b);
    if (!source || !target) return;

    var color = eventColor(event);
    var lane = i % 3;
    var curveX = Math.min(right - 26, left + 68 + lane * 24);
    var y1 = source.y;
    var y2 = target.y;
    var midY = (y1 + y2) / 2;

    appendCircle(svg, spineX, y1, 3.7, color, "event-node");
    appendCircle(svg, spineX, y2, 3.7, color, "event-node");
    appendPath(svg, "M " + spineX + " " + y1 + " C " + curveX + " " + y1 + ", " + curveX + " " + y2 + ", " + spineX + " " + y2,
      color, 1.8, eventMarker(event), "0.80", null, "presentation-link");

    if (Math.abs(y2 - y1) > 36) {
      appendText(svg, Math.min(right - 105, curveX + 4), midY - 3, eventLabel(event), color);
    }
  });
}

function renderPolyphonicOverlay(result) {
  var table = document.getElementById("utterance-table");
  var scroll = document.querySelector(".table-scroll");
  if (!table || !scroll) return;

  var old = document.getElementById("polyphonic-overlay-svg");
  if (old) old.remove();

  var topicCells = table.querySelectorAll("td.col-topic");
  var replyCells = table.querySelectorAll("td.col-reply");
  var presCells = table.querySelectorAll("td.col-presentation");
  if (!topicCells.length || !replyCells.length || !presCells.length) return;

  var tableRect = table.getBoundingClientRect();
  var scrollRect = scroll.getBoundingClientRect();
  var svg = createOverlaySvg(table, tableRect, scrollRect, scroll);
  var voices = getVoices(result);
  var events = getVisibleEvents(voices, getEvents(result)).filter(function (event) {
    return document.getElementById("utt-" + event.utterance_a) &&
          document.getElementById("utt-" + event.utterance_b);
  });
  var active = activeTopic();
  var visibleVoiceIndices = getVisibleVoiceIndices(voices);

  drawTopicLines(svg, table, tableRect, voices, visibleVoiceIndices, active);
  drawTopicToReplyLinks(svg, table, tableRect, voices, visibleVoiceIndices, events, active);
  drawSmallReplyLinks(svg, table, tableRect, events);
  drawPresentationLinks(svg, table, tableRect, presCells, events);

  scroll.style.position = "relative";
  scroll.appendChild(svg);
}
