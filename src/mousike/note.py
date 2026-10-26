"""Notes in Sowerby's URN notation.

A note is cited by a URN in ``urn:cite2:zst:`` (short form drops the prefix)
with up to five dot-separated tiers, e.g. ``gvn:11.1.1.0.0``:

1. base note
2. sharpening (1 = unsharpened, 2 = first sharp, 3 = second sharp)
3. length: 1 = no length sign, 2-5 = diseme, triseme, tetraseme, pentaseme
4. arsis: 1 if the note carries an arsis dot (stigme), else 0
5. hyphen: 1 if the note carries a hyphen, else 0

Collections are ``gvn`` (vocal), ``gin`` (instrumental) and ``gcn``
(other signs, e.g. the rest ``gcn:1``, which has only one tier).
"""

from functools import lru_cache
from importlib import resources

URN_PREFIX = "urn:cite2:zst:"
JOINER = "~"
LENGTHS = range(1, 6)


@lru_cache(maxsize=None)
def load_table() -> dict:
    """Map short URNs (``gvn:11.1``) to ``(unicode, name)`` pairs.

    Reads the symbol column (not the hex column, which has malformed entries
    in the source) and the description column of ``data/sowerby_system.cex``.
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
        urn = cols[0].strip()
        if urn.startswith(URN_PREFIX):
            urn = urn[len(URN_PREFIX):]
        table[urn] = (cols[1].strip(), cols[4].strip())
    return table


def _flag(value, tier, urn):
    if value not in ("0", "1"):
        raise ValueError(f"{urn!r}: {tier} must be 0 or 1, not {value!r}")
    return value == "1"


class Note:
    """A single note (or other sign) in Sowerby's notation.

    >>> n = Note("gvn:14.1.3.1.1")
    >>> n.length, n.arsis, n.hyphen
    (3, True, True)
    >>> n.unicode, n.name
    ('Ι', "vocal d′")

    Tiers 3-5 may be omitted, defaulting to length 1, no arsis, no hyphen.
    Raises ``ValueError`` for a malformed URN or a pitch not in the table.
    """

    __slots__ = ("collection", "base", "sharpening", "length", "arsis",
                 "hyphen", "_pitch_key")

    def __init__(self, urn: str):
        short = urn.strip()
        if short.startswith(URN_PREFIX):
            short = short[len(URN_PREFIX):]
        collection, sep, ref = short.partition(":")
        if not sep or not collection or not ref:
            raise ValueError(f"Not a note URN: {urn!r}")
        tiers = ref.split(".")
        if len(tiers) > 5 or not all(t.isdigit() for t in tiers):
            raise ValueError(f"Not a note URN: {urn!r}")

        table = load_table()
        if f"{collection}:{'.'.join(tiers[:2])}" in table and len(tiers) >= 2:
            key = f"{collection}:{tiers[0]}.{tiers[1]}"
            sharpening = int(tiers[1])
        elif f"{collection}:{tiers[0]}" in table and len(tiers) == 1:
            key, sharpening = f"{collection}:{tiers[0]}", None
        else:
            raise ValueError(f"No such note in the table: {urn!r}")

        length = int(tiers[2]) if len(tiers) > 2 else 1
        if length not in LENGTHS:
            raise ValueError(f"{urn!r}: length must be 1-5, not {length}")

        set_ = object.__setattr__
        set_(self, "collection", collection)
        set_(self, "base", int(tiers[0]))
        set_(self, "sharpening", sharpening)
        set_(self, "length", length)
        set_(self, "arsis", _flag(tiers[3], "arsis", urn) if len(tiers) > 3 else False)
        set_(self, "hyphen", _flag(tiers[4], "hyphen", urn) if len(tiers) > 4 else False)
        set_(self, "_pitch_key", key)

    def __setattr__(self, name, value):
        raise AttributeError("Note objects are immutable")

    @property
    def unicode(self) -> str:
        """Unicode string for the written sign (pitch only)."""
        return load_table()[self._pitch_key][0]

    @property
    def name(self) -> str:
        """Name from the data table, e.g. ``'vocal E'``."""
        return load_table()[self._pitch_key][1]

    @property
    def urn(self) -> str:
        """Short URN with all tiers, e.g. ``'gvn:1.1.1.0.0'``."""
        if self.sharpening is None:
            return self._pitch_key
        return (f"{self._pitch_key}.{self.length}."
                f"{int(self.arsis)}.{int(self.hyphen)}")

    @property
    def full_urn(self) -> str:
        return URN_PREFIX + self.urn

    @property
    def vocal(self) -> bool:
        return self.collection == "gvn"

    @property
    def instrumental(self) -> bool:
        return self.collection == "gin"

    def _key(self):
        return (self.collection, self.base, self.sharpening, self.length,
                self.arsis, self.hyphen)

    def __eq__(self, other):
        return isinstance(other, Note) and self._key() == other._key()

    def __hash__(self):
        return hash(self._key())

    def __str__(self):
        return self.urn

    def __repr__(self):
        return f"Note({self.urn!r})"


def parse_note_groups(notes: str) -> list:
    """Parse a notation-edition string into note groups (one per syllable).

    Whitespace separates groups; ``~`` joins notes within a group.

    >>> parse_note_groups("gvn:11.1.1.0.0 gvn:13.3.1.0.0~gvn:14.1.1.0.0")
    [[Note('gvn:11.1.1.0.0')], [Note('gvn:13.3.1.0.0'), Note('gvn:14.1.1.0.0')]]
    """
    return [[Note(n) for n in token.split(JOINER) if n] for token in notes.split()]


def parse_notes(notes: str) -> list:
    """Parse a notation-edition string into a flat list of ``Note`` objects.

    >>> parse_notes("gvn:11.1.1.0.0 gvn:13.3.1.0.0~gvn:14.1.1.0.0")
    [Note('gvn:11.1.1.0.0'), Note('gvn:13.3.1.0.0'), Note('gvn:14.1.1.0.0')]
    """
    return [n for group in parse_note_groups(notes) for n in group]
