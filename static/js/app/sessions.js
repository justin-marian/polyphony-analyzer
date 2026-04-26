"use strict";

function populateDropdown(sessions) {
    var sessionSelect = document.getElementById("session-select");
    if (!sessionSelect) return;

    sessionSelect.innerHTML =
        '<option value="">-- Pick a sample (or paste below) --</option>' +
        sessions.map(function (session) {
            var label = session.name || session.id;

            if (session.topic && label.indexOf(session.topic) === -1) {
                label += " — " + session.topic;
            }

            return (
                '<option value="' + escAttr(session.id) + '">' +
                escHtml(label) +
                '</option>'
            );
    }).join("");
}

function populateDropdownFromBuiltIn() {
    var sessions = Object.keys(SAMPLE_NAMES).map(function (id) {
        return {
            id: id,
            name: SAMPLE_NAMES[id]
        };
    });

    populateDropdown(sessions);
}

function loadSessions() {
    fetchFirstJson(SESSION_INDEX_URLS)
    .then(function (data) {
        var sessions = Array.isArray(data) ? data : (data.sessions || []);

        if (!sessions.length) {
            throw new Error("No sessions found.");
        }

        populateDropdown(sessions);
    }).catch(function () {
        populateDropdownFromBuiltIn();
    });
}

function loadSessionById(id) {
    var urls = SESSION_URL_PATTERNS.map(function (pattern) {
        return pattern.replace("{id}", encodeURIComponent(id));
    });
    return fetchFirstJson(urls);
}

function sessionToPlainText(data) {
    if (data.text) return data.text;
    var utterances = data.utterances || data.conversation || [];
    return utterances.map(function (u) {
        return String(u.speaker || "").trim() + ": " + String(u.text || "").trim();
    }).join("\n");
}

function handleSessionChange() {
    var sessionSelect = document.getElementById("session-select");
    var chatInput = document.getElementById("chat-input");

    if (!sessionSelect || !chatInput) return;

    var id = sessionSelect.value;
    if (!id) return;

    setStatus("Loading sample");

    loadSessionById(id)
    .then(function (data) {
        chatInput.value = sessionToPlainText(data);
        setStatus("Sample loaded. Click Analyze.");
    }).catch(function () {
        if (typeof SAMPLES !== "undefined" && SAMPLES[id]) {
            chatInput.value = SAMPLES[id];
            setStatus("Sample loaded. Click Analyze.");
        } else {
            setStatus("Sample not found. Check that JSON files are in /data.", true);
        }
    });
}
