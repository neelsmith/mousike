"""Align a text edition with a notational edition, syllable by note group.

Each whitespace-separated group of notes in the notational edition
(notes joined with ``~`` form one group) is sung on one syllable, so the
n-th syllable of a passage aligns with the n-th note group.

Both editions are CEX-style files: a header line, then ``urn|content``
lines. Passages are paired by the last component of their CTS URN
(the passage reference, e.g. ``1`` in ``...seikilos.text:1``).
"""

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
        """Two-line display: notes above, hyphenated syllables below."""
        cols_n, cols_s = [], []
        for s in self.syllables:
            text = s.syllable + ("" if s.word_final else "-")
            width = max(len(s.notes), len(text))
            cols_n.append(s.notes.ljust(width))
            cols_s.append(text.ljust(width))
        return "  ".join(cols_n).rstrip() + "\n" + "  ".join(cols_s).rstrip()


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
