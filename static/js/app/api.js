"use strict";

function fetchJson(url, options) {
    return fetch(url, options).then(function (res) {
    if (res.ok) return res.json();

    return res.json()
        .catch(function () { return {}; })
        .then(function (err) {
            throw new Error(err.detail || err.error || res.statusText || "Server error");
        });
    });
}

function fetchFirstJson(urls, options) {
    var index = 0;
    function tryNext() {
        if (index >= urls.length) {
            throw new Error("No JSON endpoint responded.");
        }
        return fetchJson(urls[index++], options).catch(tryNext);
    }
    return tryNext();
}

function analyzeOnServer(text, name) {
    return fetchJson("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            text: text,
            name: name
        })
    });
}
