"""Tunings: assign a frequency to each ``Note``.

Any object with a ``frequency(note) -> float | None`` method is a tuning
(``None`` for signs with no pitch, such as the rest ``gcn:1``).

``NominalTuning`` reads the notation at face value. Each base note is a
natural step of the grid E F G A B c d e ..., and its sharpenings
raise it by a quarter tone (first sharp) and a semitone (second sharp),
in 12-tone equal temperament. It is a baseline for checking the pipeline,
not a historical tuning.
"""

from math import log2
from typing import Optional, Protocol

from .note import Note
from .ptolemy import DEGREES, PtolemaicSystem

# Semitones above E for each step of a 7-note octave: E F G A B c d
_STEP_SEMITONES = (0, 1, 3, 5, 7, 8, 10)
# Cents added by sharpening 1 (natural), 2 (first sharp), 3 (second sharp)
_SHARPENING_CENTS = {1: 0.0, 2: 50.0, 3: 100.0}
# Base note 11 (a) is 17 semitones above base note 1 (E)
_A_STEP = 11


class Tuning(Protocol):
    def frequency(self, note: Note) -> Optional[float]:
        ...


def cents(ratio: float) -> float:
    """Size of a frequency ratio in cents."""
    return 1200 * log2(ratio)


def nominal_cents(note: Note) -> Optional[float]:
    """Cents of ``note`` above base note 1 (E) in the nominal reading."""
    if note.sharpening is None:
        return None
    octave, step = divmod(note.base - 1, 7)
    return (1200 * octave + 100 * _STEP_SEMITONES[step]
            + _SHARPENING_CENTS[note.sharpening])


class NominalTuning:
    """Notation at face value, with base note ``a`` at ``reference_hz``.

    >>> t = NominalTuning()
    >>> round(t.frequency(Note("gvn:11.1")), 2)
    220.0
    """

    def __init__(self, reference_hz: float = 220.0):
        self.reference_hz = reference_hz
        self._a_cents = nominal_cents(Note(f"gvn:{_A_STEP}.1"))

    def frequency(self, note: Note) -> Optional[float]:
        c = nominal_cents(note)
        if c is None:
            return None
        return self.reference_hz * 2 ** ((c - self._a_cents) / 1200)

    def __repr__(self):
        return f"NominalTuning(reference_hz={self.reference_hz})"


def midi_pitch(freq: float):
    """Nearest MIDI key to ``freq`` and the offset from it in cents.

    >>> midi_pitch(440.0)
    (69, 0.0)
    """
    m = 69 + 12 * log2(freq / 440.0)
    key = round(m)
    return key, (m - key) * 100


def bend_value(offset_cents: float, bend_range: int = 2) -> int:
    """14-bit pitch-bend value for an offset in cents (8192 = no bend)."""
    value = 8192 + round(offset_cents * 8192 / (bend_range * 100))
    return max(0, min(16383, value))


class TuningMismatch(ValueError):
    """A note's sign doesn't fit the chosen tonos and division."""


# Base note 8 (vocal e) lies on thetic hypate meson (Perfect System index 4).
_THETIC_OFFSET = 8 - DEGREES.index("hypate meson")


def thetic_index(note: Note) -> int:
    """Perfect System index of the thetic string a note is played on,
    from its base letter (e = hypate meson, a = mese, e′ = nete diezeugmenon)."""
    return note.base - _THETIC_OFFSET


def _string_name(index: int) -> str:
    if 0 <= index < len(DEGREES):
        return DEGREES[index]
    octaves, i = divmod(index, 7)
    return f"{DEGREES[i]} {octaves:+d} octave(s)"


class PtolemaicTuning:
    """Tune notes on Ptolemy's system in a given division and tonos.

    Each note is played on the thetic string named by its base letter; the
    tonos and division decide how that string is tuned. The sign's
    sharpening is only used as a check: if the tuned string is more than
    ``tolerance_cents`` from the notation read at face value, the note
    doesn't belong to this tonos/division and ``TuningMismatch`` is raised.

    Only diatonic divisions are supported so far (in chromatic and
    enharmonic, a letter and its sharps are different strings).

    >>> t = PtolemaicTuning("tense_diatonic", "phrygian")
    >>> round(t.frequency(Note("gvn:13.3")), 1)     # Κ, c♯′ on trite diezeugmenon
    275.0
    """

    def __init__(self, division, tonos, hypate_meson_hz: float = 165.0,
                 tolerance_cents: float = 60.0):
        self.system = PtolemaicSystem(division, tonos, hypate_meson_hz)
        if self.system.division.genus != "diatonic":
            raise ValueError(
                f"{self.system.division.name}: only diatonic divisions are "
                f"supported so far")
        self.tolerance_cents = tolerance_cents
        # face-value reading anchored to the same hypate meson (vocal e)
        self._nominal = NominalTuning(hypate_meson_hz * 2 ** (5 / 12))

    def deviation(self, note: Note) -> Optional[float]:
        """Cents between the tuned string and the face-value reading."""
        nominal = self._nominal.frequency(note)
        if nominal is None:
            return None
        return cents(self._tuned(note) / nominal)

    def _tuned(self, note: Note) -> float:
        ratio = self.system.thetic_index_ratio(thetic_index(note))
        return self.system.hypate_meson_hz * float(ratio)

    def string(self, note: Note) -> Optional[str]:
        """Name of the thetic string the note is played on."""
        if note.sharpening is None:
            return None
        return _string_name(thetic_index(note))

    def frequency(self, note: Note) -> Optional[float]:
        if note.sharpening is None:
            return None
        dev = self.deviation(note)
        if abs(dev) > self.tolerance_cents:
            raise TuningMismatch(
                f"{note} ({note.unicode}, {note.name}) is {dev:+.0f} cents from "
                f"{self.string(note)} in {self.system.tonos.name} "
                f"{self.system.division.name.lower()}; it doesn't fit this "
                f"tonos and division")
        return self._tuned(note)

    def __repr__(self):
        s = self.system
        return (f"PtolemaicTuning({s.division.key!r}, {s.tonos.name!r}, "
                f"hypate_meson_hz={s.hypate_meson_hz})")
