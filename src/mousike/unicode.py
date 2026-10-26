"""Map Sowerby note URNs to their Unicode representation.

A note is cited with up to five dot-separated tiers, e.g. ``gvn:11.1.1.0.0``:
base note, sharpening, length, arsis, hyphen. Only the first two tiers
(base note + sharpening) determine the written symbol, so the remaining
tiers are ignored here.

Most symbols are a single code point; symbols in the upper octave are a
base character followed by PRIME (U+2032), as defined in Sowerby's table.
"""

from functools import lru_cache
from importlib import resources

URN_PREFIX = "urn:cite2:zst:"
JOINER = "~"


@lru_cache(maxsize=None)
def load_pitch_table() -> dict:
    """Return a dict mapping short URNs (``gvn:11.1``) to Unicode strings.

    The symbol column of the table is used (not the hex column), since it is
    the authoritative rendering and some hex entries in the source are
    malformed.
    """
    text = (
        resources.files("mousike")
        .joinpath("data/sowerby_system.cex")
        .read_text(encoding="utf-8")
    )
    table = {}
    for line in text.splitlines()[1:]:
        if not line.strip():
            continue
        cols = line.split("|")
        urn, symbol = cols[0].strip(), cols[1].strip()
        if urn.startswith(URN_PREFIX):
            urn = urn[len(URN_PREFIX):]
        table[urn] = symbol
    return table


def _short_urn(note: str) -> str:
    note = note.strip()
    if note.startswith(URN_PREFIX):
        note = note[len(URN_PREFIX):]
    return note


def note_to_unicode(note: str) -> str:
    """Return the Unicode symbol for a single note URN.

    >>> note_to_unicode("gvn:11.1.1.0.0")
    'Ϲ'
    """
    short = _short_urn(note)
    try:
        collection, ref = short.split(":", 1)
    except ValueError:
        raise ValueError(f"Not a valid note URN: {note!r}") from None
    tiers = ref.split(".")
    table = load_pitch_table()
    # Pitches are keyed on two tiers; other signs (e.g. the rest gcn:1) on one.
    for n in (2, 1):
        key = f"{collection}:{'.'.join(tiers[:n])}"
        if len(tiers) >= n and key in table:
            return table[key]
    raise KeyError(f"No Unicode symbol for note {note!r}")


def notes_to_unicode(notes: str) -> str:
    """Convert a whitespace-separated list of note URNs to Unicode.

    Notes are separated by a single space, except that notes joined with
    ``~`` (several notes over one syllable) are written with no space.

    >>> notes_to_unicode("gvn:11.1.1.0.0 gvn:13.3.1.0.0~gvn:14.1.1.0.0")
    'Ϲ ΚΙ'
    """
    groups = []
    for token in notes.split():
        groups.append("".join(note_to_unicode(n) for n in token.split(JOINER) if n))
    return " ".join(groups)
