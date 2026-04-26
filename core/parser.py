from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from core.config import SPEAKER_SEPARATORS
from core.models import Utterance


TIMESTAMP_PREFIX_RE = re.compile(r"^\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*")
REPLY_REF_RE = re.compile(r"\(reply\s+to\s+(\d+)\)", re.IGNORECASE)
SPEAKER_SEP_RE = re.compile(
    r"^([A-Za-z0-9_\-\. ]+?)\s*(?:" +
    "|".join(re.escape(s) for s in SPEAKER_SEPARATORS) +
    r")\s*(.+)$")


def parse_chat_log(source: str | Path | dict[str, Any]) -> list[Utterance]:
    """
    Parse a chat log and return an ordered list of Utterance objects.

    source can be a Path, a raw text string, a JSON string, or a dict
    containing an utterances/conversation field. Raises ValueError if no
    parseable utterances are found.
    """
    if isinstance(source, dict):
        utterances = parse_json_object(source)
    else:
        raw = load_text(source)
        utterances = parse_json_text(raw) or parse_lines(raw.splitlines())

    if not utterances:
        raise ValueError(
            "No valid utterances found. Expected text like 'Speaker: message' "
            "or JSON with an 'utterances' array.")
    return utterances


def load_text(source: str | Path) -> str:
    """
    Read source into a string.

    When source is a Path or a string naming an existing file, the file is
    read from disk. Otherwise source is treated as inline content.
    """
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8")

    candidate = Path(str(source))
    if "\n" not in str(source) and candidate.exists():
        return candidate.read_text(encoding="utf-8")

    return str(source)


def load_lines(source: str | Path) -> list[str]:
    """
    Backwards-compatible helper returning raw lines from text or file input.
    """
    return load_text(source).splitlines()


def parse_json_text(raw: str) -> list[Utterance]:
    """
    Try to parse raw text as JSON and return utterances if successful.
    Returns an empty list when the text is not JSON or has no conversation.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    if isinstance(data, dict):
        return parse_json_object(data)
    if isinstance(data, list):
        return parse_json_utterances(data)
    return []


def parse_json_object(data: dict[str, Any]) -> list[Utterance]:
    """
    Convert a JSON session object into Utterance objects.

    Supported keys are utterances, conversation, and sessions. If a combined
    sessions file is supplied, the first session is parsed by default.
    """
    if "utterances" in data:
        return parse_json_utterances(data["utterances"])

    if "conversation" in data:
        return parse_json_utterances(data["conversation"])

    if "sessions" in data and data["sessions"]:
        first = data["sessions"][0]
        if isinstance(first, dict):
            return parse_json_object(first)

    return []


def parse_json_utterances(items: Any) -> list[Utterance]:
    """
    Convert a list of JSON utterance dictionaries into Utterance objects.
    """
    if not isinstance(items, list):
        return []

    utterances: list[Utterance] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        speaker = str(item.get("speaker", "")).strip()
        text = str(item.get("text", "")).strip()
        if not speaker or not text:
            continue

        reply_to_raw = item.get("reply_to")
        reply_to: Optional[int]
        if reply_to_raw is None or reply_to_raw == "":
            reply_to = None
        else:
            reply_to = int(reply_to_raw)

        utterances.append(Utterance(
            index=len(utterances),
            speaker=speaker,
            text=text,
            reply_to=reply_to))

    return utterances


def parse_lines(lines: list[str]) -> list[Utterance]:
    """
    Convert raw text lines into Utterance objects.

    Blank lines, comments, and lines not matching the expected
    speaker-separator-message pattern are skipped.
    """
    utterances: list[Utterance] = []

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        line = TIMESTAMP_PREFIX_RE.sub("", line).strip()
        match = SPEAKER_SEP_RE.match(line)
        if not match:
            continue

        speaker = match.group(1).strip()
        text = match.group(2).strip()

        reply_to: Optional[int] = None
        ref_match = REPLY_REF_RE.search(text)
        if ref_match:
            reply_to = int(ref_match.group(1))
            text = REPLY_REF_RE.sub("", text).strip()

        utterances.append(Utterance(
            index=len(utterances),
            speaker=speaker,
            text=text,
            reply_to=reply_to))

    return utterances
