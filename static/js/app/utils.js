"use strict";

function escHtml(value) {
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
function escAttr(value) { return escHtml(value); }
function numberOr(value, fallback) { return typeof value === "number" ? value : fallback; }

function uniqueSorted(values) {
    var seen = {};
    values.forEach(function (value) {
        if (value !== undefined && value !== null && value !== "") {
            seen[value] = true;
        }
    });
    return Object.keys(seen).sort();
}

function setStatus(message, isError) {
    var statusEl = document.getElementById("status");
    if (!statusEl) return;
    statusEl.textContent = message || "";
    statusEl.className = "status" + (isError ? " error" : "");
}
