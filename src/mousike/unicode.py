"""Render note URNs as Unicode strings.

Only the first two tiers (base note + sharpening) determine the written
symbol. Most symbols are a single code point; symbols in the upper octave
are a base character followed by PRIME (U+2032), as in Sowerby's table.
"""

from .note import Note, load_table, parse_note_groups


def load_pitch_table() -> dict:
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
