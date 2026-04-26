from __future__ import annotations

import json
from pathlib import Path

from core.models import PolyphonicAnalysisResult


def generate_text_report(result: PolyphonicAnalysisResult) -> str:
    """Build a simplified text report (no convergence/divergence)."""
    return "\n\n".join([
        build_header(result),
        build_voices(result),
        build_speaker_stats(result),
        build_utterances_preview(result)
    ])


def save_text_report(result: PolyphonicAnalysisResult, output_dir: Path) -> Path:
    """Save the plain-text report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{safe_filename(result.chat_log_name)}.txt"
    path.write_text(generate_text_report(result), encoding="utf-8")
    return path


def save_json_report(result: PolyphonicAnalysisResult, output_dir: Path) -> Path:
    """Save JSON report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{safe_filename(result.chat_log_name)}.json"
    path.write_text(json.dumps(result_to_dict(result), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def build_header(result: PolyphonicAnalysisResult) -> str:
    sep = "=" * 60
    speakers = sorted({u.speaker for u in result.utterances})

    return (
        f"{sep}\n"
        f"SESSION: {result.chat_log_name.upper()}\n"
        f"{sep}\n"
        f"Utterances : {len(result.utterances)}\n"
        f"Speakers   : {', '.join(speakers)}\n"
        f"Voices     : {len(result.voices)}")


def build_voices(result: PolyphonicAnalysisResult) -> str:
    lines = ["-- VOICES " + "-" * 48]

    if not result.voices:
        lines.append("No voices detected.")
        return "\n".join(lines)

    for i, v in enumerate(result.voices, 1):
        lines.extend([
            f"\nVoice {i}: {v.label}",
            f"  Frequency : {v.frequency}",
            f"  Speakers  : {', '.join(v.speakers)}",
            f"  Occurrences: {v.utterance_indices[:6]}"
        ])

    return "\n".join(lines)


def build_speaker_stats(result: PolyphonicAnalysisResult) -> str:
    lines = ["-- SPEAKER STATS " + "-" * 42]

    for speaker, stats in result.speaker_stats.items():
        lines.extend([
            f"\n{speaker}",
            f"  Utterances : {stats.get('utterance_count', 0)}",
            f"  Avg tokens : {stats.get('avg_length', 0):.1f}",
            f"  Voices     : {', '.join(stats.get('voices_contributed', [])) or '-'}"
        ])

    return "\n".join(lines)


def build_utterances_preview(result: PolyphonicAnalysisResult) -> str:
    lines = ["-- UTTERANCES PREVIEW " + "-" * 34]

    for u in result.utterances[:10]:
        lines.append(f"{u.index:02d}. {u.speaker}: {short(u.text)}")

    if len(result.utterances) > 10:
        lines.append("...")

    return "\n".join(lines)


def result_to_dict(result: PolyphonicAnalysisResult) -> dict:
    return {
        "chat_log_name": result.chat_log_name,
        "utterances": [{
            "index": u.index,
            "speaker": u.speaker,
            "text": u.text
        } for u in result.utterances],
        "voices": [{
            "label": v.label,
            "frequency": v.frequency,
            "speakers": v.speakers
        } for v in result.voices],
        "speaker_stats": result.speaker_stats
    }

def short(text: str, n: int = 80) -> str:
    text = text.replace("\n", " ").strip()
    return text if len(text) <= n else text[:n - 3] + "..."


def safe_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
