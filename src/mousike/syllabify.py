"""Syllabify ancient Greek text.

Rules (standard ancient Greek syllable division):

* every syllable has exactly one nucleus: a vowel or a diphthong
  (αι ει οι υι αυ ευ ηυ ου ωυ; a diaeresis on the second vowel breaks it);
* a single consonant between nuclei begins the next syllable;
* in a consonant cluster, the longest tail that can begin a Greek word goes
  with the following syllable, the rest closes the preceding one
  (so ε-στι, χρο-νος, but ἄλ-λος, ἄγ-γελος);
* word-initial and word-final consonants join the first/last syllable.

Works on NFC or NFD input, with or without accents and breathings; output
is NFC. Lunate sigma and final sigma are treated as sigma.
"""

import unicodedata

VOWELS = set("αεηιουω")
DIPHTHONGS = {"αι", "ει", "οι", "υι", "αυ", "ευ", "ηυ", "ου", "ωυ"}
DIAERESIS = "̈"

# Consonant clusters that can begin a word, and so begin a syllable.
ONSETS = set("""
βδ βλ βρ γλ γν γρ δμ δν δρ θλ θμ θν θρ κλ κμ κν κρ κτ μν
πλ πν πρ πτ σβ σθ σκ σμ σπ στ σφ σχ τλ τμ τρ φθ φλ φν φρ χθ χλ χμ χν χρ
σκλ σκρ σπλ σπρ στρ σφρ σχρ
""".split())

_SIGMAS = {"ς": "σ", "ϲ": "σ", "Ϲ": "σ"}


def _units(word):
    """Split a word into (base_letter, full_text) units, keeping combining
    marks with the letter they modify."""
    units = []
    for ch in unicodedata.normalize("NFD", word):
        if unicodedata.combining(ch) and units:
            base, text = units[-1]
            units[-1] = (base, text + ch)
        else:
            base = _SIGMAS.get(ch, ch.lower())
            units.append((base, ch))
    return units


def _is_vowel(unit):
    return unit[0] in VOWELS


def _is_letter(unit):
    return unicodedata.category(unit[0]).startswith("L")


def _nuclei(units):
    """Return (start, end) index pairs (end exclusive) of syllable nuclei."""
    nuclei = []
    i = 0
    while i < len(units):
        if _is_vowel(units[i]):
            nxt = units[i + 1] if i + 1 < len(units) else None
            if (nxt is not None and units[i][0] + nxt[0] in DIPHTHONGS
                    and DIAERESIS not in nxt[1]):
                nuclei.append((i, i + 2))
                i += 2
                continue
            nuclei.append((i, i + 1))
        i += 1
    return nuclei


def _onset_split(cluster):
    """Index in the cluster at which the next syllable begins."""
    for k in range(len(cluster)):
        tail = "".join(cluster[k:])
        if len(tail) == 1 or tail in ONSETS:
            return k
    return len(cluster)


def syllabify_word(word):
    """Divide one word into syllables.

    >>> syllabify_word("απαιτει")
    ['α', 'παι', 'τει']
    """
    units = _units(word)
    # Hold leading/trailing punctuation aside and re-attach it afterwards.
    start = 0
    while start < len(units) and not _is_letter(units[start]):
        start += 1
    end = len(units)
    while end > start and not _is_letter(units[end - 1]):
        end -= 1
    lead = "".join(u[1] for u in units[:start])
    trail = "".join(u[1] for u in units[end:])
    core = units[start:end]

    nuclei = _nuclei(core)
    if len(nuclei) <= 1:
        sylls = ["".join(u[1] for u in core)] if core else []
    else:
        bounds = [0]
        for (_, prev_end), (next_start, _) in zip(nuclei, nuclei[1:]):
            cluster = [u[0] for u in core[prev_end:next_start]]
            bounds.append(prev_end + _onset_split(cluster))
        bounds.append(len(core))
        sylls = ["".join(u[1] for u in core[a:b])
                 for a, b in zip(bounds, bounds[1:])]

    if not sylls:
        sylls = [""]
    sylls[0] = lead + sylls[0]
    sylls[-1] = sylls[-1] + trail
    return [unicodedata.normalize("NFC", s) for s in sylls if s]


def syllabify(text):
    """Syllabify a passage: a list of words, each a list of syllables.

    >>> syllabify("οσον ζης φαινου")
    [['ο', 'σον'], ['ζης'], ['φαι', 'νου']]
    """
    return [syllabify_word(w) for w in text.split()]
