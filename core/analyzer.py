"""
Polyphonic Analysis Engine.

Step 1 - Utterance delimitation
Step 2 - Link identification
Step 3 - Voice identification 
Step 4 - Inter-animation detection
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Optional

from core.config import (
    CONCESSION_PIVOTS,
    CONVERGENCE_MARKERS, DIVERGENCE_MARKERS,
    MAX_VOICES, MIN_VOICES,
    SIMILARITY_THRESHOLD, STRONG_CONVERGENCE_OPENERS,
    VOICE_MIN_FREQUENCY)
from core.models import (
    InterAnimationEvent,
    PolyphonicAnalysisResult,
    Utterance, Voice)
from core.text_utils import (
    build_tfidf_matrix, cosine_similarity,
    find_concession_pivot, find_discourse_marker,
    find_strong_opener, tokenize)


class PolyphonicAnalyzer:
    """
    Runs the complete polyphonic analysis pipeline on a parsed chat log.

    The analyze method is the only public entry point. All helper methods
    are plain (non-private) methods so that subclasses can override 
    individual steps without touching the others.
    """

    def analyze(
        self,
        utterances: list[Utterance],
        chat_log_name: str = "chat") -> PolyphonicAnalysisResult:
        """Run all four steps of the Polyphonic Analysis Method and return the aggregated result."""
        if not utterances:
            raise ValueError("Cannot analyse an empty conversation.")

        # Tokenise each utterance in-place before any other step
        enrich_tokens(utterances)
        # Build a graph of similarity and reply links
        tfidf_vectors, _ = build_tfidf_matrix([u.text for u in utterances])
        links = self.identify_links(utterances, tfidf_vectors)
        # Extract thematic voices from recurring content words
        voices = self.identify_voices(utterances)
        # Classify inter-animation events along every link
        events = self.detect_inter_animation(utterances, links, voices)

        speaker_stats = compute_speaker_stats(utterances, voices, events)
        voice_graph = {v.label: v.utterance_indices for v in voices}

        return PolyphonicAnalysisResult(
            chat_log_name=chat_log_name,
            utterances=utterances, voices=voices,
            inter_animation_events=events,
            speaker_stats=speaker_stats,
            voice_graph=voice_graph)

    def identify_links(
        self,
        utterances: list[Utterance],
        vectors: list[dict[str, float]]) -> dict[int, list[int]]:
        """
        Build a backward link graph between utterances.

        Each utterance may link to earlier ones in three ways. An
        explicit reply_to reference takes priority. Any pair whose
        TF-IDF cosine similarity exceeds SIMILARITY_THRESHOLD is also
        linked (within a 10-utterance lookback window).

        As a final fallback, any utterance with no link of either kind is linked to its immediate predecessor. 

        This matters for short chat turns where stop-word removal leaves almost no shared
        vocabulary without the fallback, conversational reactions like "Yeah, that works." 
        would have no link to react against and would never produce an inter-animation event.

        Returns a dict mapping utterance index to the list of earlier indices it is connected to.
        """
        links: dict[int, list[int]] = defaultdict(list)

        for i, utterance in enumerate(utterances):
            if utterance.reply_to is not None and utterance.reply_to < i:
                links[i].append(utterance.reply_to)

            for j in range(max(0, i - 10), i):
                if j in links[i]:
                    continue
                sim = cosine_similarity(vectors[i], vectors[j])
                if sim >= SIMILARITY_THRESHOLD:
                    links[i].append(j)

            # Every utterance after the first should react to something. 
            # Default to the immediate predecessor when nothing else linked.
            if i > 0 and not links[i]:
                links[i].append(i - 1)

        return dict(links)

    def identify_voices(self, utterances: list[Utterance]) -> list[Voice]:
        """
        Extract between MIN_VOICES and MAX_VOICES thematic voices.

        A voice in the Bakhtinian sense is a recurring concept that gets
        re-voiced by participants across the conversation.
        Here each voice is anchored to a content word that appears in at least
        VOICE_MIN_FREQUENCY distinct utterances.

        Candidates are ranked by frequency multiplied by speaker diversity
        so that words shared between multiple participants rank higher than
        words used by only one speaker. Returns voices in descending rank order.
        """
        term_occurrences: dict[str, list[int]] = defaultdict(list)
        term_speakers: dict[str, list[str]] = defaultdict(list)

        for utterance in utterances:
            seen: set[str] = set()
            for token in utterance.tokens:
                if token not in seen:
                    term_occurrences[token].append(utterance.index)
                    term_speakers[token].append(utterance.speaker)
                    seen.add(token)

        candidates = {term: indices for term, indices in term_occurrences.items() if len(indices) >= VOICE_MIN_FREQUENCY}

        if not candidates:
            # For very short conversations: take the most frequent terms.
            all_counts = Counter({t: len(v) for t, v in term_occurrences.items()})
            candidates = {t: term_occurrences[t] for t, _ in all_counts.most_common(MIN_VOICES)}

        def voice_score(term: str) -> float:
            freq = len(candidates[term])
            diversity = len(set(term_speakers[term]))
            return freq * diversity

        top_terms = sorted(candidates, key=voice_score, reverse=True)[:MAX_VOICES]

        voices: list[Voice] = []
        for term in top_terms:
            indices = candidates[term]
            speakers = list(dict.fromkeys(term_speakers[term]))
            voices.append(Voice(
                label=term,
                utterance_indices=indices,
                speakers=speakers,
                frequency=len(indices)))

        return voices

    def detect_inter_animation(
        self,
        utterances: list[Utterance],
        links: dict[int, list[int]],
        voices: list[Voice]) -> list[InterAnimationEvent]:
        """
        Identify divergence and convergence events across all links.

        For each pair of linked utterances from different speakers the
        text of the later utterance is scanned for discourse markers.

        A divergence marker produces a divergence event; a convergence
        marker produces a convergence event; neutral text is skipped.

        The voices_involved field of each event lists the voice labels
        that both utterances in the pair belong to.
        """
        utterance_voice_map: dict[int, list[str]] = defaultdict(list)
        for voice in voices:
            for idx in voice.utterance_indices:
                utterance_voice_map[idx].append(voice.label)

        events: list[InterAnimationEvent] = []

        for utterance_b in utterances:
            for linked_idx in links.get(utterance_b.index, []):
                utterance_a = utterances[linked_idx]
                if utterance_a.speaker == utterance_b.speaker:
                    continue

                kind, trigger = classify_relation(utterance_b.text)
                if kind is None:
                    continue

                involved = list(
                    set(utterance_voice_map.get(utterance_a.index, [])) | 
                    set(utterance_voice_map.get(utterance_b.index, [])))

                events.append(InterAnimationEvent(
                    kind=kind,
                    utterance_a=utterance_a.index,
                    utterance_b=utterance_b.index,
                    speaker_a=utterance_a.speaker,
                    speaker_b=utterance_b.speaker,
                    trigger_word=trigger,
                    voices_involved=involved))

        return events


def enrich_tokens(utterances: list[Utterance]) -> None:
    """
    Tokenize the text of every utterance and store the result in-place.
    Must be called before identify_voices or detect_inter_animation.
    """
    for utterance in utterances:
        utterance.tokens = tokenize(utterance.text)


def classify_relation(text: str) -> tuple[Optional[str], str]:
    """
    Classify the relation an utterance has with the one it links back to.

    Detection order (most specific first, so we don't double-fire):

    1. Explicit disagreement phrases ("i disagree", "i don't agree", "not really") -- unambiguous divergence.
    2. Strong convergence opener at the very start of the utterance
        ("Yeah,", "Right.", "Agreed."). If a concession pivot follows
        ("...but...", "...though"), we still call it a convergence
        because the speaker first granted the predecessor's claim --
        in the polyphonic model the "yes, but" pattern is a
        convergence with a divergent extension, not a pure divergence.
        Surface this with the trigger 'opener+pivot' so reports can
        flag it as a soft / partial convergence.
    3. Generic divergence markers ("however", "instead", "rather", "differ", "contrary", ...).
    4. Generic convergence markers ("agreed", "exactly", "good point", ...).

    Returns ("divergence" | "convergence" | None, trigger_word).
    """
    opener = find_strong_opener(text, STRONG_CONVERGENCE_OPENERS)
    if opener:
        pivot = find_concession_pivot(
            text,
            CONCESSION_PIVOTS,
            skip=len(opener.split())
        )

        if pivot:
            return "divergence", f"{opener}+{pivot}"

        return "convergence", opener

    div_trigger = find_discourse_marker(text, DIVERGENCE_MARKERS)
    if div_trigger:
        return "divergence", div_trigger

    conv_trigger = find_discourse_marker(text, CONVERGENCE_MARKERS)
    if conv_trigger:
        return "convergence", conv_trigger

    return None, ""


def compute_speaker_stats(
    utterances: list[Utterance], voices: list[Voice],
    events: list[InterAnimationEvent]) -> dict[str, dict]:
    """
    Build a per-speaker metrics dict from utterances, voices, and events.

    Each speaker entry contains utterance_count, avg_length in tokens,
    voices_contributed as a sorted list of voice labels, and counts of
    divergences and convergences the speaker initiated.
    """
    stats: dict[str, dict] = defaultdict(lambda: {
        "utterance_count": 0, "avg_length": 0.0, "voices_contributed": set(),
        "divergences_initiated": 0, "convergences_initiated": 0
    })

    for utterance in utterances:
        stats[utterance.speaker]["utterance_count"] += 1
        stats[utterance.speaker]["avg_length"] += len(utterance.tokens)

    for speaker in stats:
        count = stats[speaker]["utterance_count"]
        if count:
            stats[speaker]["avg_length"] /= count

    for voice in voices:
        for speaker in voice.speakers:
            stats[speaker]["voices_contributed"].add(voice.label)

    for event in events:
        if event.kind == "divergence":
            stats[event.speaker_b]["divergences_initiated"] += 1
        else:
            stats[event.speaker_b]["convergences_initiated"] += 1

    for speaker in stats:
        stats[speaker]["voices_contributed"] = sorted(stats[speaker]["voices_contributed"])

    return dict(stats)
