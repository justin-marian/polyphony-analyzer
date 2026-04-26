# Polyphonic Analyzer - Web UI

A small FastAPI wrapper around your existing `core/` polyphonic analyzer,
plus a plain HTML/CSS/JS frontend (no React, no TypeScript, no build step).

## Run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open <http://127.0.0.1:8000>.

## What you can do

- Pick one of the 6 bundled sample sessions from the dropdown, or
- Paste your own chat log into the textarea (one line per utterance,
  format: `Speaker: message`), and
- Click **Analyze** to see voices, divergences, convergences, and
  per-speaker stats rendered next to the highlighted utterance table.

## Adding more sessions

Drop a `.txt` file into `data/` named `session_<something>.txt` and add an
entry to `SAMPLE_SESSIONS` in `main.py`.
