"use strict";

var SESSION_INDEX_URLS = [
    "/api/sessions",
    "/data/sessions_index.json",
    "data/sessions_index.json",
    "sessions_index.json"
];

var SESSION_URL_PATTERNS = [
    "/api/sessions/{id}",
    "/data/{id}.json",
    "data/{id}.json",
    "{id}.json"
];

var SAMPLE_NAMES = {
    session_hh1: "Human-Human 1 (Creativity)",
    session_hh2: "Human-Human 2 (Ethics)",
    session_hc1: "Human-Chatbot 1 (AGI)",
    session_hc2: "Human-Chatbot 2 (Consciousness)",
    session_cc1: "Chatbot-Chatbot 1 (Creativity)",
    session_cc2: "Chatbot-Chatbot 2 (AGI)"
};
