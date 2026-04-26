"""
FastAPI server that wraps the Polyphonic Analyzer.

Run locally with:
    pip install -r requirements.txt
    uvicorn main:app --reload

Then open http://127.0.0.1:8000 in your browser.

Endpoints:
    GET  /                  -> the static frontend (index.html)
    GET  /api/sessions      -> list of bundled sample sessions
    GET  /api/sessions/{id} -> raw text of one sample session
    POST /api/analyze       -> run the analyzer on chat text and return JSON
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.analyzer import PolyphonicAnalyzer
from core.parser import parse_chat_log


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"


SAMPLE_SESSIONS = [
    {"id": "session_hh1", "name": "Human-Human 1 (Creativity)"},
    {"id": "session_hh2", "name": "Human-Human 2 (AGI)"},
    {"id": "session_hc1", "name": "Human-Chatbot 1 (Creativity)"},
    {"id": "session_hc2", "name": "Human-Chatbot 2 (Ethics)"},
    {"id": "session_cc1", "name": "Chatbot-Chatbot 1 (Consciousness)"},
    {"id": "session_cc2", "name": "Chatbot-Chatbot 2 (AGI)"}
]


app = FastAPI(title="Polyphonic Analyzer")


class AnalyzeRequest(BaseModel):
    text: str
    name: str = "Pasted Chat"


def result_to_dict(result) -> dict:
    """
    Convert a PolyphonicAnalysisResult into a plain dict that the frontend
    can render. Mirrors the structure used by core/reporter.py but trimmed
    to what the UI actually needs.
    """
    return {
        "name": result.chat_log_name,
        "summary": {
            "utterances": len(result.utterances),
            "speakers": sorted({u.speaker for u in result.utterances}),
            "voices": len(result.voices),
            "divergences": len(result.divergences),
            "convergences": len(result.convergences),
        },
        "utterances": [ {
            "index": u.index,
            "speaker": u.speaker,
            "text": u.text,
            "tokens": u.tokens,
            "reply_to": u.reply_to
        } for u in result.utterances],
        "voices": [asdict(v) for v in result.voices],
        "events": [asdict(e) for e in result.inter_animation_events],
        "speaker_stats": result.speaker_stats,
        "voice_graph": result.voice_graph
    }


def run_analysis(text: str, name: str) -> dict:
    """Parse, analyse, and serialise a chat log string."""
    utterances = parse_chat_log(text)
    analyzer = PolyphonicAnalyzer()
    result = analyzer.analyze(utterances, chat_log_name=name)
    return result_to_dict(result)


@app.get("/api/sessions")
def list_sessions() -> list[dict]:
    """Return the list of bundled sample sessions available on disk."""
    available = []
    for s in SAMPLE_SESSIONS:
        if (DATA_DIR / f"{s['id']}.txt").exists():
            available.append(s)
    return available


@app.get("/api/sessions/{session_id}")
def get_session_text(session_id: str) -> dict:
    """Return the raw text of one sample session so the user can preview it."""
    path = DATA_DIR / f"{session_id}.txt"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return {"id": session_id, "text": path.read_text(encoding="utf-8")}


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest) -> dict:
    """Run the polyphonic analyzer on the supplied chat text."""
    try:
        return run_analysis(req.text, req.name or "Pasted Chat")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/data", StaticFiles(directory="data"), name="data")


@app.get("/")
def index() -> FileResponse:
    return FileResponse("index.html")
