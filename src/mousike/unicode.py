"""Render note URNs as Unicode strings.

The first two tiers (base note + sharpening) choose the written sign;
length (diseme to pentaseme) and arsis are added as combining marks (see
``Note.unicode``). The hyphen tier is not rendered. Most symbols are a single code point; symbols in the upper octave
are a base character followed by PRIME (U+2032), as in Sowerby's table.
"""

import re

from .note import JOINER, URN_PREFIX, Note, load_table, parse_note_groups

_ONE_URN = rf"(?:{re.escape(URN_PREFIX)})?(?:gvn|gin|gcn):\d+(?:\.\d+)*"
# A note URN, or several joined with ``~``, standing on its own in running
# text (not part of a longer word or URN).
NOTE_URN_RE = re.compile(
    rf"(?<![\w:.]){_ONE_URN}(?:{re.escape(JOINER)}{_ONE_URN})*(?![\w:~]|\.\d)")


def load_pitch_table() -> dict:  # bare pitch signs, without marks
    """Map short URNs (``gvn:11.1``) to Unicode strings."""
    return {k: sym for k, (sym, _) in load_table().items()}


def note_to_unicode(note: str) -> str:
    """Return the Unicode symbol for a single note URN.

    >>> note_to_unicode("gvn:11.1.1.0.0")
    'Ϲ'
    """
    return Note(note).unicode


def groups_to_unicode(groups) -> str:
    """Render note groups: space between groups, none within a group."""
    return " ".join("".join(n.unicode for n in g) for g in groups)


def notes_to_unicode(notes: str) -> str:
    """Convert a notation-edition string to Unicode.

    Notes are separated by a single space, except that notes joined with
    ``~`` (several notes over one syllable) are written with no space.

    >>> notes_to_unicode("gvn:11.1.1.0.0 gvn:13.3.1.0.0~gvn:14.1.1.0.0")
    'Ϲ ΚΙ'
    """
    return groups_to_unicode(parse_note_groups(notes))


def note_urn_spans(text: str) -> list:
    """Split running text into spans, converting note URNs to Unicode.

    Returns a list of ``(source, unicode, error)`` triples covering the
    whole text in order:

    * plain text: ``(source, None, None)``
    * a note URN, or ``~``-joined URNs: ``(source, unicode, None)``
    * something shaped like a note URN that isn't in Sowerby's table:
      ``(source, None, message)``

    Both full (``urn:cite2:zst:gvn:11.1``) and short (``gvn:11.1``) URNs
    are recognized.

    >>> note_urn_spans("ὅσον gvn:11.1.1.0.0!")
    [('ὅσον ', None, None), ('gvn:11.1.1.0.0', 'Ϲ', None), ('!', None, None)]
    """
    spans, pos = [], 0
    for m in NOTE_URN_RE.finditer(text):
        if m.start() > pos:
            spans.append((text[pos:m.start()], None, None))
        try:
            uni = "".join(Note(u).unicode for u in m.group().split(JOINER))
            spans.append((m.group(), uni, None))
        except ValueError as e:
            spans.append((m.group(), None, str(e)))
        pos = m.end()
    if pos < len(text):
        spans.append((text[pos:], None, None))
    return spans


def urns_to_unicode(text: str) -> str:
    """Replace every note URN in running text with its Unicode sign.
    URNs not in Sowerby's table are left as they are.

    >>> urns_to_unicode("Notes: gvn:11.1 gvn:13.3~gvn:14.1.")
    'Notes: Ϲ ΚΙ.'
    """
    return "".join(uni if uni is not None else src
                   for src, uni, _ in note_urn_spans(text))
