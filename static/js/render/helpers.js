"use strict";


var VOICE_COLORS = ["#f59e0b", "#0ea5e9", "#22c55e", "#ec4899", "#8b5cf6"];
var ACTIVE_TOPIC_LABEL = null;

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, function (c) {
    return {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    }[c];
  });
}
function escAttr(value) { return esc(value); }
function escRe(value) { return String(value ?? "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }

function getVoices(result) { return result.voices || []; }
function getEvents(result) {   return result.inter_animation_events || result.events || []; }

function topicKey(label) { return String(label || "").trim().toLowerCase(); }
function activeTopic() { return ACTIVE_TOPIC_LABEL ? topicKey(ACTIVE_TOPIC_LABEL) : null; }

function eventColor(event) { return event.kind === "divergence" ? "#dc2626" : "#16a34a"; }
function eventMarker(event) { return event.kind === "divergence" ? "arr-red-small" : "arr-green-small"; }
function eventLabel(event) { return event.kind === "divergence" ? "Divergence" : "Convergence"; }

function chip(label, value) { return '<span class="chip">' + label + ': <strong>' + esc(value) + '</strong></span>'; }
function chipCol(label, value, color) {
  return (
    '<span class="chip chip-colored" style="border-color:' + color + '">' +
      label + ': <strong style="color:' + color + '">' + esc(value) + '</strong>' +
    '</span>'
  );
}
