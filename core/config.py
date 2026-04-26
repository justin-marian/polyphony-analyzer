"""
Configuration constants for the Polyphonic Analyzer.

All tunable parameters and domain-specific word lists are defined here.
Changing a value here propagates automatically to every module that
imports it - no magic numbers are scattered across the codebase.

Word lists are tuned to the Polyphonic Analysis Method where
divergence corresponds to a centrifugal/dissonant force between voices
and convergence to a centripetal/consonant one. Discourse markers are
only one of several signals - negation flips, concession patterns, and
shared-voice clash also feed the classifier in analyzer.py.
"""

try:
    from nltk.corpus import stopwords
    BASE_STOP_WORDS: set[str] = set(stopwords.words("english"))
except LookupError:
    import nltk
    nltk.download("stopwords", quiet=True)
    from nltk.corpus import stopwords
    BASE_STOP_WORDS: set[str] = set(stopwords.words("english"))

SPEAKER_SEPARATORS: tuple[str, ...] = (":", "-", ">")

DOMAIN_STOP_WORDS: set[str] = {
    # Conversational hedges and agreement particles
    "yes", "yeah", "yep", "ok", "okay", "fine", "fair",
    "maybe", "perhaps", "probably", "actually", "indeed",
    "really", "just", "sure", "right", "true",
    # Discourse connectives
    "because", "since", "while", "during", "before", "after",
    "then", "now", "still", "though", "however", "therefore",
    "thus", "hence", "consequently", "moreover", "furthermore",
    "additionally", "also", "although", "yet", "nevertheless",
    "nonetheless",
    # Generic verbs
    "think", "know", "mean", "make", "want", "going", "get", "go",
    "say", "said", "tell", "told", "see", "seen", "look", "let",
    "seem", "seems", "seemed", "use", "used", "using",
    # Generic nouns / filler terms
    "thing", "things", "something", "anything", "everything",
    "way", "point", "part", "kind", "sort", "lot",
    # Number words
    "one", "two", "three", "four", "five",
    # Common tokenizer contraction fragments
    "let's", "i'd", "i'll", "i've", "i'm",
    "you're", "they're", "we're", "it's", "that's", "there's",
    # Explicit contractions
    "doesn't", "don't", "isn't", "aren't", "wasn't", "weren't",
    "won't", "wouldn't", "shouldn't", "couldn't", "can't"
}

STOP_WORDS: frozenset[str] = frozenset(BASE_STOP_WORDS | DOMAIN_STOP_WORDS)

# Discourse markers - DIVERGENCE
# Centrifugal markers signalling contrast, opposition, or disagreement.
# Common single-word offenders ("but", "not", "no") are deliberately
# excluded because they appear inside concession openers ("Agreed, but...")
# and inside negated agreements ("not wrong"), producing false divergences.
# Multi-word phrases stay because their oppositional intent is robust to
# surrounding context.
DIVERGENCE_MARKERS: frozenset[str] = frozenset({
    "however", "although", "though", "whereas",
    "nevertheless", "nonetheless", "contrary", "disagree",
    "instead", "differ", "unlike", "against", "oppose",
    "rather", "alternatively", "conversely",
    "on the contrary", "on the other hand", "in contrast",
    "i disagree", "that is wrong", "i do not agree",
    "i don't agree", "not really", "not exactly"
})

# Discourse markers - CONVERGENCE
# Centripetal markers signalling agreement, elaboration, or alignment.
# Causal connectors ("so", "because", "since") are excluded because they
# fire inside divergent utterances too. Strong opener words ("right", "true", "sure") 
# live in STRONG_CONVERGENCE_OPENERS instead so they only count when positioned at the start of an utterance.
CONVERGENCE_MARKERS: frozenset[str] = frozenset({
    "agreed", "agree", "absolutely", "exactly", "indeed",
    "precisely", "correct", "certainly", "of course",
    "accept", "converge", "consensus",
    "moreover", "furthermore", "additionally",
    "similarly", "likewise", "as well", "in addition",
    "therefore", "thus", "hence", "consequently",
    "good point", "fair point", "well said"
})

# STRONG opener words - position-sensitive convergence anchors
# These words signal convergence ONLY when they appear within the first
# OPENER_WINDOW tokens. They are deliberately separated from the general
# CONVERGENCE_MARKERS list because they routinely appear mid-sentence with
# a non-convergent meaning ("right now", "true creativity").
# 
# At the opener position, they often anchor a concession pattern: "Yes, but..."
# opens with agreement, then pivots. Whether the overall utterance is a
# convergence or a divergence depends on what follows the pivot
STRONG_CONVERGENCE_OPENERS: frozenset[str] = frozenset({
    "agreed", "agree", "absolutely", "exactly", "indeed",
    "precisely", "correct", "certainly", "yes", "yeah", "yep",
    "right", "true", "sure", "of course",
    "ok", "okay", "fine", "fair"
})

# Concession pivots
# Words that, when they appear AFTER a strong convergence opener, flip
# the utterance from convergence into divergence ("yes, BUT chats
# encourage involvement"). This is the inter-animation pattern shown
# explicitly in the Trausan-Matu polyphonic example (slide 18 of the
# Polyphonic Model paper): michael says "yes, but chats encourage
# involvement" - this is a divergence dressed as agreement.
CONCESSION_PIVOTS: frozenset[str] = frozenset({
    "but", "however", "although", "though", "yet",
    "still", "nevertheless", "nonetheless"
})

# Negation markers - used for semantic opposition detection
# When a shared voice appears with negation in B but not in A (or vice
# versa), that is treated as a semantic divergence even if no discourse
# marker is present. This catches "creativity requires rules" vs
# "creativity does not require rules" - a clear divergence with no
# explicit "but" or "however".
NEGATION_TOKENS: frozenset[str] = frozenset({
    "not", "no", "never", "none", "nothing", "neither",
    "nor", "cannot", "without", "lack", "lacks",
    "doesn't", "don't", "isn't", "aren't", "wasn't", "weren't",
    "won't", "wouldn't", "shouldn't", "couldn't", "can't"
})

# Voice extraction parameters
# A word becomes a voice candidate when it appears in at least
# VOICE_MIN_FREQUENCY distinct utterances. 
# MAX_VOICES keeps downstream rendering compact.
# MIN_VOICES is a floor for short logs.
VOICE_MIN_FREQUENCY: int = 2
MAX_VOICES: int = 2
MIN_VOICES: int = 4

# Cosine threshold above which two utterances are considered semantically
# linked even without an explicit reply_to reference. The lookback window
# bounds the cost of similarity computation.
SIMILARITY_THRESHOLD: float = 0.15
LINK_LOOKBACK: int = 10

# Inter-animation classification thresholds
# A score above CONVERGENCE_THRESHOLD becomes a convergence;
# a score below DIVERGENCE_THRESHOLD becomes a divergence.
# Anything in between is treated as neutral and discarded.
CONVERGENCE_THRESHOLD: float = 0.5
DIVERGENCE_THRESHOLD: float = -0.5

# Number of opening tokens inspected for strong convergence openers and
# concession pivots. 4 catches "Yes, but ...", "Agreed, although ...",
# while staying small enough to avoid mid-sentence false matches.
OPENER_WINDOW: int = 4
