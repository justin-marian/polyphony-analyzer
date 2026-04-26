from __future__ import annotations

import math
import re
from collections import Counter
from typing import Optional

from core.config import NEGATION_TOKENS, OPENER_WINDOW, STOP_WORDS

# Captures alphabetic word forms including apostrophe contractions.
# Used by tokenize for content words and by the marker / opener helpers
# (which keep stop-words because "yes", "but", "not" matter for them).
TOKEN_RE = re.compile(r"[a-zA-Z']+")


def tokenize(text: str) -> list[str]:
    """
    Split text into lowercase content words, removing stop-words and
    single-character tokens. Returns a list of meaningful word tokens
    suitable for voice extraction and TF-IDF vectorisation.
    """
    raw = TOKEN_RE.findall(text.lower())
    return [w for w in raw if w not in STOP_WORDS and len(w) > 1]


def raw_tokens(text: str) -> list[str]:
    """
    Return the full lowercase token sequence WITHOUT removing stop-words.
    Needed for marker and negation detection because words like "but",
    "not", "yes" are stop-words for voice extraction but essential here.
    """
    return [t for t in TOKEN_RE.findall(text.lower()) if len(t) > 0]


def token_set(text: str) -> set[str]:
    """Return the unique set of content tokens for the given text."""
    return set(tokenize(text))


def build_tfidf_matrix(documents: list[str],) -> tuple[list[dict[str, float]], list[str]]:
    """
    Compute TF-IDF vectors for a list of documents.

    Returns a pair (vectors, vocab). vectors is a list of dicts mapping
    each term to its TF-IDF score for that document. vocab is the sorted
    list of all terms that appear across the corpus.
    """
    tokenized = [tokenize(doc) for doc in documents]
    vocab = sorted({t for doc in tokenized for t in doc})
    n_docs = len(documents)

    doc_freq: Counter[str] = Counter()
    for tokens in tokenized:
        doc_freq.update(set(tokens))

    vectors: list[dict[str, float]] = []
    for tokens in tokenized:
        term_freq = Counter(tokens)
        total = len(tokens) or 1
        vec: dict[str, float] = {}
        for term in set(tokens):
            tf_score = term_freq[term] / total
            idf_score = math.log((1 + n_docs) / (1 + doc_freq[term])) + 1.0
            vec[term] = tf_score * idf_score
        vectors.append(vec)

    return vectors, vocab


def cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """
    Compute cosine similarity between two sparse TF-IDF vectors.
    Returns a float in the range [0.0, 1.0].
    """
    common = set(vec_a) & set(vec_b)
    if not common:
        return 0.0

    dot = sum(vec_a[t] * vec_b[t] for t in common)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))

    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def find_discourse_marker(text: str, marker_set: frozenset[str]) -> Optional[str]:
    """
    Search text for any marker from marker_set and return the first match.

    Longer phrases are checked before shorter ones so that a phrase like
    "on the contrary" wins over the single word "contrary" when both are
    present in the same utterance. Word boundaries are enforced so that
    "but" inside "tribute" does not match. Returns None when no marker
    is found.
    """
    lower = text.lower()
    for marker in sorted(marker_set, key=len, reverse=True):
        pattern = r"\b" + re.escape(marker) + r"\b"
        if re.search(pattern, lower):
            return marker
    return None


def opener_tokens(text: str, window: int = OPENER_WINDOW) -> list[str]:
    """
    Return the first window tokens of text, lowercased, INCLUDING
    stop-words. We keep stop-words here because the openers we care
    about ("yes", "but", "no") are themselves stop-words.
    """
    return raw_tokens(text)[:window]


def find_strong_opener(text: str, opener_set: frozenset[str]) -> Optional[str]:
    """
    Look for any opener word from opener_set within the first `window`
    tokens, but ONLY when the opener is clearly delimited from the rest
    of the utterance.

    A bare "True creativity matters" should NOT fire as an opener -
    "true" there is just an adjective, not an agreement marker. We
    require the opener to be followed by sentence-ending or clause-
    ending punctuation (comma, period, semicolon, exclamation, dash,
    em-dash, en-dash) in the original text, OR for the opener to BE
    the entire opening clause (the utterance starts with "Yes." or
    "Agreed.").

    A leading hesitation token ("hmm", "well", "so", "look", "okay")
    followed by punctuation is skipped before the search, so that
    "Hmm, fair." still resolves to opener="fair". Without this skip,
    informal chat replies that begin with a filler would never match.

    Multi-word openers like "of course" must match a sliding window of
    consecutive tokens. Returns the matched opener or None.
    """
    if not text:
        return None

    lowered = text.strip().lower()

    # Strip a leading hesitation marker like "hmm," or "well," so that
    # the real opener (often the next word) becomes reachable.
    HESITATIONS = ("hmm", "well", "so", "look", "okay", "ok")
    for hes in HESITATIONS:
        # Match the hesitation followed by clause-terminating
        # punctuation, then any whitespace.
        m = re.match(
            r"^\s*" + re.escape(hes) + r"\b[\s,.;:!?\u2013\u2014\-]+",
            lowered)
        if m:
            lowered = lowered[m.end():]
            break

    sorted_openers = sorted(opener_set, key=lambda s: -len(s.split()))

    # Words whose meaning at sentence-start is unambiguously agreement,
    # even without a punctuation delimiter. "Agreed for high-stakes."
    # is clearly convergence; "right now we should..." is not. We only
    # waive the punctuation requirement for words in this small set.
    UNAMBIGUOUS = {"agreed", "agree", "absolutely", "exactly", "indeed", "precisely", "of course"}

    for opener in sorted_openers:
        if opener in UNAMBIGUOUS:
            # Match the opener as the first word, followed by space,
            # punctuation, or end of string. No punctuation required.
            pattern = r"^\s*" + re.escape(opener) + r"\b"
        else:
            # Positional openers must be delimited from the rest of
            # the utterance to avoid false positives like "true
            # creativity matters" or "fair criticism".
            pattern = (r"^\s*" + re.escape(opener) +  r"\b(?=\s*(?:[,.;:!?\u2013\u2014\-]|$))")
        if re.search(pattern, lowered):
            return opener

    return None


def find_concession_pivot(
    text: str,
    pivot_set: frozenset[str],
    skip: int = 1) -> Optional[str]:
    """
    After matching a strong convergence opener, look for a concession
    pivot ("but", "however", ...) somewhere AFTER the opener position.

    We deliberately do not require it to be adjacent: "Yes, I agree
    completely, but I also worry about chaos" is still a concession
    pattern even with a long agreement clause before "but". `skip`
    is how many opener tokens to skip past before searching.
    """
    tokens = raw_tokens(text)
    if len(tokens) <= skip:
        return None

    rest = tokens[skip:]
    for pivot in pivot_set:
        if pivot in rest:
            return pivot
    return None


def has_negated_term(text: str, target: str, distance: int = 4) -> bool:
    """
    Return True when target appears within `distance` tokens of a
    negation cue in text. This is a deliberately shallow approximation
    of negation scope - it catches "creativity is not free" and "no
    creativity exists here", which is what we need for divergence
    detection.

    A more rigorous parse-tree-based implementation would require a
    full dependency parser; this rule-based version stays accurate
    enough for short conversational turns while keeping the engine
    dependency-free.
    """
    if not target:
        return False
    tokens = raw_tokens(text)
    contractions_with_nt = [t for t in tokens if t.endswith("n't")]
    target_lower = target.lower()

    for i, tok in enumerate(tokens):
        if tok != target_lower:
            continue
        window_start = max(0, i - distance)
        window_end = min(len(tokens), i + distance + 1)
        window = tokens[window_start:window_end]
        for w in window:
            if w in NEGATION_TOKENS or w in contractions_with_nt:
                return True
    return False


def count_voice_overlap(voices_a: set[str], voices_b: set[str]) -> int:
    """
    Return the number of voices both utterances re-voice. In Bakhtin's
    sense an inter-animation event requires shared subject matter -
    two utterances that talk about completely disjoint topics cannot
    diverge or converge with one another, even if a discourse marker
    happens to appear.
    """
    return len(voices_a & voices_b)
