"""Align a text edition with a notational edition, syllable by note group.

Each whitespace-separated group of notes in the notational edition
(notes joined with ``~`` form one group) is sung on one syllable, so the
n-th syllable of a passage aligns with the n-th note group.

Both editions are CEX-style files: a header line, then ``urn|content``
lines. Passages are paired by the last component of their CTS URN
(the passage reference, e.g. ``1`` in ``...seikilos.text:1``).

``align_syllables`` instead aligns a syllable edition (one syllable per
line, cited ``passage.n``, a trailing ``-`` marking a syllable that does
not end its word) with the notational edition: syllables are grouped by
passage and paired with that passage's note groups in order.
"""

import unicodedata
from dataclasses import dataclass, field

from .syllabify import syllabify
from .note import parse_note_groups


@dataclass
class AlignedSyllable:
    syllable: str
    notes: str          # Unicode rendering of the note group
    word_index: int     # which word of the passage the syllable belongs to
    word_final: bool    # True if the syllable ends its word
    note_group: list = field(default_factory=list)  # the Note objects


@dataclass
class AlignedPassage:
    ref: str
    syllables: list

    def __str__(self):
        """Two-line display: notes above, hyphenated syllables below.
        Columns are padded by visible width (combining marks take no space)."""
        cols_n, cols_s = [], []
        for s in self.syllables:
            text = s.syllable + ("" if s.word_final else "-")
            width = max(_width(s.notes), _width(text))
            cols_n.append(s.notes + " " * (width - _width(s.notes)))
            cols_s.append(text + " " * (width - _width(text)))
        return "  ".join(cols_n).rstrip() + "\n" + "  ".join(cols_s).rstrip()


def _width(text: str) -> int:
    """Number of visible characters (combining marks don't count)."""
    return sum(1 for ch in text if not unicodedata.combining(ch))


class AlignmentError(ValueError):
    pass


def align_passage(text, notes, ref=""):
    """Align one passage of text with its note string."""
    words = syllabify(text)
    sylls = [(s, wi, si == len(w) - 1)
             for wi, w in enumerate(words) for si, s in enumerate(w)]
    groups = parse_note_groups(notes)
    if len(sylls) != len(groups):
        raise AlignmentError(
            f"Passage {ref or '?'}: {len(sylls)} syllables "
            f"({'-'.join(s for s, _, _ in sylls)}) but {len(groups)} note groups"
        )
    return AlignedPassage(ref, [
        AlignedSyllable(s, "".join(n.unicode for n in g), wi, final, g)
        for (s, wi, final), g in zip(sylls, groups)
    ])


def read_cex(path):
    """Read ``urn|content`` lines into a dict keyed by passage reference."""
    with open(path, encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip()]
    passages = {}
    for line in lines[1:]:
        urn, content = line.split("|", 1)
        passages[urn.rsplit(":", 1)[-1]] = content
    return passages


def align_editions(text_path, notes_path):
    """Align every passage present in both editions, in text-edition order."""
    texts = read_cex(text_path)
    notes = read_cex(notes_path)
    return [align_passage(texts[ref], notes[ref], ref)
            for ref in texts if ref in notes]


def group_syllables(syllables):
    """Group a syllable edition (``{"1.1": "ο-", "1.2": "σον", ...}``, as
    returned by ``read_cex``) by passage: ``{"1": ["ο-", "σον", ...]}``.
    The passage is the reference minus its last level; order is kept."""
    passages = {}
    for ref, syll in syllables.items():
        if "." not in ref:
            raise ValueError(f"Not a syllable-level reference: {ref}")
        passages.setdefault(ref.rsplit(".", 1)[0], []).append(syll)
    return passages


def align_syllable_passage(syllables, notes, ref=""):
    """Align a passage's syllables (strings; a trailing ``-`` marks a syllable
    that does not end its word) with its note string, one note group each."""
    groups = parse_note_groups(notes)
    if len(syllables) != len(groups):
        raise AlignmentError(
            f"Passage {ref or '?'}: {len(syllables)} syllables "
            f"({' '.join(syllables)}) but {len(groups)} note groups"
        )
    aligned, word = [], 0
    for syll, g in zip(syllables, groups):
        syll = syll.strip()
        final = not syll.endswith("-")
        aligned.append(AlignedSyllable(syll.rstrip("-"), "".join(n.unicode for n in g),
                                       word, final, g))
        if final:
            word += 1
    return AlignedPassage(ref, aligned)


def align_syllables(syllables_path, notes_path):
    """Align a syllable edition (one ``urn|syllable`` line per syllable,
    cited ``passage.n``) with a notational edition, passage by passage, in
    syllable-edition order. Passages missing from either edition are skipped."""
    sylls = group_syllables(read_cex(syllables_path))
    notes = read_cex(notes_path)
    return [align_syllable_passage(sylls[ref], notes[ref], ref)
            for ref in sylls if ref in notes]
