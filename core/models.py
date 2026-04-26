from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Utterance:
    """
    A single conversational turn.

    index is the zero-based position in the chat log.
    speaker holds the participant name exactly as written in the log.
    text is the raw message content after stripping metadata.
    tokens is filled by the analyzer during preprocessing.
    reply_to is the index of a previous utterance this one explicitly
    references, or None when no explicit reference is present.
    """
    index: int
    speaker: str
    text: str
    tokens: list[str] = field(default_factory=list)
    reply_to: Optional[int] = None

    def __repr__(self) -> str:
        preview = self.text[:60].replace("\n", " ")
        return f"Utterance({self.index}, {self.speaker!r}, {preview!r})"


@dataclass
class Voice:
    """
    A thematic thread in the Bakhtinian sense.

    In the Polyphonic Model a voice is anchored to a recurring concept
    (a word or short phrase) that is re-voiced across the conversation
    by one or more speakers. The label is the key concept, frequency
    counts how many utterances carry it, and speakers lists every
    participant who contributed to this voice in order of first appearance.

    The strength field is frequency multiplied by speaker diversity,
    matching notion that voices can be "stronger or weaker" depending on how widely they are re-voiced.
    """
    label: str
    utterance_indices: list[int]
    speakers: list[str]
    frequency: int = 0
    strength: float = 0.0

    def __repr__(self) -> str:
        return (f"Voice({self.label!r}, freq={self.frequency}, "
                f"strength={self.strength:.1f}, speakers={self.speakers})")


@dataclass
class InterAnimationEvent:
    """
    A detected divergence or convergence between two utterances.

    Divergence corresponds to a centrifugal (dissonant) force in the
    musical metaphor. Convergence corresponds to a centripetal (consonant) force.
    ---
    utterance_a is the earlier utterance index, utterance_b is the
    later one that reacts to it. trigger_word is the most salient
    discourse marker that contributed to the classification (or
    "negation flip", "concession pivot", etc. for non-marker signals).
    ---
    voices_involved lists the voice labels that BOTH utterances share,
    not just the union - a true inter-animation event must re-voice at
    least one shared voice.
    ---
    confidence is a float in [0, 1] derived from the signed signal
    ---
    score: high confidence means many signals agreed on the kind, low
    confidence means the event was a borderline call. signals lists
    the human-readable signal names that fired (e.g. "marker:however",
    "concession:but-after-yes", "negation_flip:creativity").
    """
    kind: str
    utterance_a: int
    utterance_b: int
    speaker_a: str
    speaker_b: str
    trigger_word: str
    voices_involved: list[str] = field(default_factory=list)
    confidence: float = 1.0
    signals: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"InterAnimation({self.kind}, "
            f"u{self.utterance_a}->u{self.utterance_b}, "
            f"trigger={self.trigger_word!r}, "
            f"conf={self.confidence:.2f})")


@dataclass
class PolyphonicAnalysisResult:
    """
    The complete output of one polyphonic analysis run.
    ---
    chat_log_name is the label used in reports.
    ---
    utterances holds the full parsed conversation.
    ---
    voices is the list of extracted thematic threads.
    ---
    inter_animation_events contains all divergence and convergence
    ---
    events found between linked utterances.
    ---
    speaker_stats maps each participant name to a dict of metrics.
    ---
    voice_graph maps each voice label to the list of utterance indices
    that belong to it, mirroring the information in voices but keyed
    for fast lookup.
    """
    chat_log_name: str
    utterances: list[Utterance]
    voices: list[Voice]
    inter_animation_events: list[InterAnimationEvent]
    speaker_stats: dict[str, dict]
    voice_graph: dict[str, list[int]]

    @property
    def divergences(self) -> list[InterAnimationEvent]:
        """All inter-animation events classified as divergences."""
        return [e for e in self.inter_animation_events if e.kind == "divergence"]

    @property
    def convergences(self) -> list[InterAnimationEvent]:
        """All inter-animation events classified as convergences."""
        return [e for e in self.inter_animation_events if e.kind == "convergence"]
